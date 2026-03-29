#!/usr/bin/env python3
"""Patch script for server.py - optimization 3 (incremental index) and 5 (BM25 hybrid search)"""

TARGET = "/home/jet/semantic_cache/server.py"

# Read original file
with open(TARGET) as f:
    content = f.read()

# ====== ADD GLOBAL BM25 VARS after text_store ======
old_text = """index = None
text_store = []  # 每条: {"text": str, "role": str, "type": str, "timestamp": str}

# 增量索引：记录已处理的文件和最后修改时间
_file_mtime_cache = {}"""

new_text = """index = None
text_store = []  # 每条: {"text": str, "role": str, "type": str, "timestamp": str}

# 增量索引：记录已处理的文件和最后修改时间
_file_mtime_cache = {}

# ====== 优化5: BM25 混合检索 ======
bm25_index = {}  # dict[str, list[int]] - 词 → 文档ID列表
_bm25_doc_freq = {}  # 词 → 文档频率（用于IDF计算）

def _simple_tokenize(text):
    """简单分词器：空格/标点分割，中文按字符bigram"""
    import re
    # 转小写
    text = text.lower()
    # 移除非字母数字的字符
    text = re.sub(r'[^a-z0-9\u4e00-\u9fff]', ' ', text)
    words = text.split()
    # 中文bigram
    chinese = re.findall(r'[\u4e00-\u9fff]+', text)
    tokens = words[:]
    for seg in chinese:
        for i in range(len(seg) - 1):
            tokens.append(seg[i:i+2])
        if seg:
            tokens.append(seg)  # 单字
    return tokens

def _build_bm25(entries):
    """构建 BM25 倒排索引"""
    global bm25_index, _bm25_doc_freq
    bm25_index = {}
    _bm25_doc_freq = {}
    for doc_id, entry in enumerate(entries):
        text = entry["text"]
        tokens = _simple_tokenize(text)
        seen = set()
        for token in tokens:
            if token not in seen:
                seen.add(token)
                if token not in bm25_index:
                    bm25_index[token] = []
                bm25_index[token].append(doc_id)
    for token, doc_ids in bm25_index.items():
        _bm25_doc_freq[token] = len(doc_ids)

def _bm25_score(query, doc_id, entries):
    """计算 query 对 doc_id 的 BM25 score"""
    N = len(entries)
    if N == 0:
        return 0.0
    tokens = _simple_tokenize(query)
    k1 = 1.5
    b = 0.75
    avgdl = sum(len(_simple_tokenize(e["text"])) for e in entries) / max(N, 1)
    score = 0.0
    for token in tokens:
        if token not in bm25_index or doc_id not in bm25_index[token]:
            continue
        df = _bm25_doc_freq.get(token, 0)
        idf = max(0, (N - df + 0.5) / (df + 0.5))
        # count token in doc
        doc_tokens = _simple_tokenize(entries[doc_id]["text"])
        tf = doc_tokens.count(token)
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * len(doc_tokens) / max(avgdl, 1))
        score += idf * numerator / max(denominator, 0.01)
    return score

def _bm25_normalize(scores):
    """将 BM25 scores 归一化到 [0,1]"""
    if not scores:
        return scores
    mx = max(scores)
    mn = min(scores)
    if mx == mn:
        return [1.0] * len(scores) if mx > 0 else scores
    return [(s - mn) / (mx - mn) for s in scores]"""

assert old_text in content, "Could not find text_store block to patch"
content = content.replace(old_text, new_text)

# ====== MODIFY build_index to build BM25 ======
old_build = """def build_index(entries):
    global index, text_store, _file_mtime_cache

    if not entries:
        print("无文本可索引")
        return

    texts = [e["text"] for e in entries]
    text_store = entries

    print(f"正在索引 {len(texts)} 条文本 (维度={dimension})...")
    emb = model.encode(texts, batch_size=32, show_progress_bar=True)
    faiss.normalize_L2(emb)

    index = faiss.IndexFlatIP(dimension)
    index.add(emb)

    faiss.write_index(index, f"{INDEX_DIR}/index.faiss")
    with open(f"{INDEX_DIR}/texts.json", "w") as f:
        json.dump(text_store, f, ensure_ascii=False)

    type_counts = {}
    for e in entries:
        t = e["msg_type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    print(f"索引完成: {index.ntotal} 条")
    print("类型统计:", type_counts)"""

new_build = """def build_index(entries):
    global index, text_store, _file_mtime_cache

    if not entries:
        print("无文本可索引")
        return

    texts = [e["text"] for e in entries]
    text_store = entries

    print(f"正在索引 {len(texts)} 条文本 (维度={dimension})...")
    emb = model.encode(texts, batch_size=32, show_progress_bar=True)
    faiss.normalize_L2(emb)

    index = faiss.IndexFlatIP(dimension)
    index.add(emb)

    # 优化5: 构建 BM25 倒排索引
    _build_bm25(entries)

    faiss.write_index(index, f"{INDEX_DIR}/index.faiss")
    with open(f"{INDEX_DIR}/texts.json", "w") as f:
        json.dump(text_store, f, ensure_ascii=False)

    type_counts = {}
    for e in entries:
        t = e["msg_type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    print(f"索引完成: {index.ntotal} 条")
    print("类型统计:", type_counts)"""

assert old_build in content, "Could not find build_index block to patch"
content = content.replace(old_build, new_build)

# ====== MODIFY search to support hybrid mode ======
old_search = """@app.route("/search", methods=["POST"])
def search():
    data = request.json
    q = data.get("query", "")
    k = data.get("top_k", 5)
    th = data.get("threshold", 0.3)
    msg_type_filter = data.get("type", None)

    # 任务2: 查询扩展
    q = expand_query(q)

    q_emb = model.encode([q])
    faiss.normalize_L2(q_emb)
    dists, ids = index.search(q_emb, k * 3 if k > 5 else k * 2)

    results = []
    for d, i in zip(dists[0], ids[0]):
        if i >= len(text_store):
            continue
        entry = text_store[i]
        raw_sim = float(d)
        # 任务3: 时间衰减加权
        boosted_sim = max(0, raw_sim + time_boost(entry))
        if boosted_sim < th:
            continue
        if msg_type_filter and entry["msg_type"] != msg_type_filter:
            continue
        results.append({
            "text": entry["text"],
            "role": entry["role"],
            "msg_type": entry["msg_type"],
            "timestamp": entry["timestamp"],
            "similarity": boosted_sim,
            "raw_similarity": raw_sim,
            "time_boost": time_boost(entry),
            "session": entry.get("session", "")[:8],
        })
        if len(results) >= k:
            break

    return jsonify({
        "query": q,
        "results": results,
        "total": index.ntotal,
        "hit_count": len(results),
    })"""

new_search = """@app.route("/search", methods=["POST"])
def search():
    data = request.json
    q = data.get("query", "")
    k = data.get("top_k", 5)
    th = data.get("threshold", 0.3)
    msg_type_filter = data.get("type", None)
    mode = data.get("mode", "vector")  # "vector" or "hybrid"

    # 任务2: 查询扩展
    q = expand_query(q)

    q_emb = model.encode([q])
    faiss.normalize_L2(q_emb)
    search_k = k * 3 if k > 5 else k * 2
    dists, ids = index.search(q_emb, search_k)

    # 优化5: 混合检索 - 计算 BM25 scores
    bm25_scores = []
    if mode == "hybrid" and text_store:
        bm25_scores = [_bm25_score(q, int(i), text_store) for i in ids[0]]
        bm25_norm = _bm25_normalize(bm25_scores)

    results = []
    for idx, (d, i) in enumerate(zip(dists[0], ids[0])):
        if i >= len(text_store):
            continue
        entry = text_store[i]
        raw_sim = float(d)
        # 任务3: 时间衰减加权
        boosted_sim = max(0, raw_sim + time_boost(entry))

        # 优化5: 混合得分 = 0.7*FAISS + 0.3*BM25
        if mode == "hybrid" and bm25_scores:
            bm25_val = bm25_norm[idx] if idx < len(bm25_norm) else 0.0
            final_score = 0.7 * boosted_sim + 0.3 * bm25_val
        else:
            final_score = boosted_sim

        if final_score < th:
            continue
        if msg_type_filter and entry["msg_type"] != msg_type_filter:
            continue

        result = {
            "text": entry["text"],
            "role": entry["role"],
            "msg_type": entry["msg_type"],
            "timestamp": entry["timestamp"],
            "similarity": final_score,
            "raw_similarity": raw_sim,
            "time_boost": time_boost(entry),
            "session": entry.get("session", "")[:8],
        }
        if mode == "hybrid":
            result["faiss_sim"] = boosted_sim
            result["bm25_sim"] = bm25_norm[idx] if idx < len(bm25_norm) else 0.0
        results.append(result)
        if len(results) >= k:
            break

    return jsonify({
        "query": q,
        "results": results,
        "total": index.ntotal,
        "hit_count": len(results),
        "mode": mode,
    })"""

assert old_search in content, "Could not find search block to patch"
content = content.replace(old_search, new_search)

# ====== MODIFY reindex to support incremental mode ======
old_reindex = """@app.route("/reindex", methods=["POST"])
def reindex():
    global index, text_store, _file_mtime_cache

    sessions_dir = os.path.expanduser("~/.openclaw/agents/main/sessions")
    if not os.path.exists(sessions_dir):
        return jsonify({"status": "error", "message": "sessions dir not found"}), 404

    changed_files = []
    all_files = {}
    for jf in glob.glob(f"{sessions_dir}/*.jsonl"):
        mtime = os.path.getmtime(jf)
        fname = os.path.basename(jf)
        all_files[fname] = mtime
        if fname not in _file_mtime_cache or _file_mtime_cache[fname] < mtime:
            changed_files.append(jf)

    deleted_files = set(_file_mtime_cache.keys()) - set(all_files.keys())

    if not changed_files and not deleted_files:
        return jsonify({"status": "ok", "new_entries": 0, "message": "no changes"})

    entries, file_count = load_sessions()
    if entries:
        build_index(entries)

    _file_mtime_cache = all_files

    return jsonify({
        "status": "ok",
        "new_entries": len(entries),
        "total": index.ntotal if index else 0,
        "changed_files": len(changed_files),
        "deleted_files": len(deleted_files),
        "file_count": file_count,
    })"""

new_reindex = """@app.route("/reindex", methods=["POST"])
def reindex():
    global index, text_store, _file_mtime_cache, bm25_index, _bm25_doc_freq

    sessions_dir = os.path.expanduser("~/.openclaw/agents/main/sessions")
    if not os.path.exists(sessions_dir):
        return jsonify({"status": "error", "message": "sessions dir not found"}), 404

    mode = request.args.get("mode", "full")  # "full" or "incremental"

    changed_files = []
    all_files = {}
    for jf in glob.glob(f"{sessions_dir}/*.jsonl"):
        mtime = os.path.getmtime(jf)
        fname = os.path.basename(jf)
        all_files[fname] = mtime
        if fname not in _file_mtime_cache or _file_mtime_cache[fname] < mtime:
            changed_files.append(jf)

    deleted_files = set(_file_mtime_cache.keys()) - set(all_files.keys())

    if not changed_files and not deleted_files:
        return jsonify({"status": "ok", "new_entries": 0, "message": "no changes", "mode": mode})

    if mode == "incremental" and index is not None and not deleted_files:
        # ====== 优化3: 增量索引 ======
        print(f"增量索引模式: {len(changed_files)} 个文件变化")
        new_entries = []

        for jf in changed_files:
            fname = os.path.basename(jf)
            with open(jf) as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        obj_type = obj.get("type", "")
                        timestamp = obj.get("timestamp", "")[:19]
                        session_id = fname.split('.')[0]

                        if obj_type == "message":
                            msg = obj.get("message", {})
                            role = msg.get("role", "unknown")
                            content = msg.get("content", [])
                            for c in content:
                                if isinstance(c, dict):
                                    ctype = c.get("type", "")
                                    if ctype == "text" and c.get("text"):
                                        text = c["text"].strip()
                                        if text:
                                            new_entries.append({
                                                "text": f"[{role}][消息]{text[:500]}",
                                                "role": role,
                                                "msg_type": "text",
                                                "timestamp": timestamp,
                                                "session": session_id,
                                            })
                                    elif ctype == "tool_result":
                                        tool_name = c.get("source", {}).get("tool", "unknown") if isinstance(c.get("source"), dict) else "tool"
                                        tool_text = ""
                                        if isinstance(c.get("content"), str):
                                            tool_text = c["content"]
                                        elif isinstance(c.get("content"), list):
                                            for item in c.get("content"):
                                                if isinstance(item, dict) and item.get("type") == "text":
                                                    tool_text += item.get("text", "")
                                        elif isinstance(c.get("content"), dict):
                                            tool_text = str(c.get("content", ""))[:500]
                                        if tool_text:
                                            new_entries.append({
                                                "text": f"[{role}][工具结果:{tool_name}]{tool_text[:500]}",
                                                "role": role,
                                                "msg_type": "tool_result",
                                                "timestamp": timestamp,
                                                "session": session_id,
                                            })
                                    elif ctype == "image":
                                        new_entries.append({
                                            "text": f"[{role}][图片]{c.get('source', {}).get('media_type', 'image') if isinstance(c.get('source'), dict) else 'image'}",
                                            "role": role,
                                            "msg_type": "image",
                                            "timestamp": timestamp,
                                            "session": session_id,
                                        })
                        elif obj_type == "tool_result":
                            tool_text = ""
                            content = obj.get("content", "")
                            if isinstance(content, str):
                                tool_text = content
                            elif isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict) and item.get("type") == "text":
                                        tool_text += item.get("text", "")
                            tool_name = obj.get("source", {}).get("tool", "unknown") if isinstance(obj.get("source"), dict) else "tool"
                            if tool_text:
                                new_entries.append({
                                    "text": f"[助手][工具:{tool_name}]{tool_text[:500]}",
                                    "role": "assistant",
                                    "msg_type": "tool_result",
                                    "timestamp": timestamp,
                                    "session": session_id,
                                })
                        elif obj_type == "thinking":
                            thinking_text = obj.get("data", {}).get("content", "") if isinstance(obj.get("data"), dict) else str(obj.get("data", ""))[:500]
                            if thinking_text:
                                new_entries.append({
                                    "text": f"[助手][思考]{thinking_text[:500]}",
                                    "role": "assistant",
                                    "msg_type": "thinking",
                                    "timestamp": timestamp,
                                    "session": session_id,
                                })
                        elif obj_type == "custom":
                            custom_type = obj.get("customType", obj.get("custom_type", "unknown"))
                            custom_data = obj.get("data", {})
                            if isinstance(custom_data, dict):
                                if custom_type == "model-snapshot":
                                    custom_text = f"模型切换到 {custom_data.get('modelId', 'unknown')}"
                                elif custom_type == "command":
                                    custom_text = f"命令: {custom_data.get('command', '')} {custom_data.get('args', '')}"
                                else:
                                    custom_text = f"[{custom_type}]{str(custom_data)[:200]}"
                            else:
                                custom_text = f"[{custom_type}]{str(custom_data)[:200]}"
                            new_entries.append({
                                "text": custom_text,
                                "role": "system",
                                "msg_type": f"custom:{custom_type}",
                                "timestamp": timestamp,
                                "session": session_id,
                            })
                        elif obj_type in ("session", "model_change", "thinking_level_change"):
                            info = f"[系统][{obj_type}]"
                            if obj_type == "model_change":
                                info += f" 模型: {obj.get('provider','')}/{obj.get('modelId','')}"
                            elif obj_type == "thinking_level_change":
                                info += f" 思考等级: {obj.get('thinkingLevel','')}"
                            new_entries.append({
                                "text": info,
                                "role": "system",
                                "msg_type": obj_type,
                                "timestamp": timestamp,
                                "session": session_id,
                            })
                    except Exception:
                        pass

        if new_entries:
            print(f"增量索引: 添加 {len(new_entries)} 条新记录")
            texts = [e["text"] for e in new_entries]
            emb = model.encode(texts, batch_size=32, show_progress_bar=False)
            faiss.normalize_L2(emb)
            index.add(emb)
            text_store.extend(new_entries)
            # 更新 BM25 索引
            start_id = len(text_store) - len(new_entries)
            for doc_id, entry in enumerate(new_entries, start=start_id):
                tokens = _simple_tokenize(entry["text"])
                seen = set()
                for token in tokens:
                    if token not in seen:
                        seen.add(token)
                        if token not in bm25_index:
                            bm25_index[token] = []
                        bm25_index[token].append(doc_id)
            for token in seen:
                _bm25_doc_freq[token] = len(bm25_index[token])

            # 保存
            faiss.write_index(index, f"{INDEX_DIR}/index.faiss")
            with open(f"{INDEX_DIR}/texts.json", "w") as f:
                json.dump(text_store, f, ensure_ascii=False)

        _file_mtime_cache = all_files
        return jsonify({
            "status": "ok",
            "mode": "incremental",
            "new_entries": len(new_entries),
            "total": index.ntotal if index else 0,
            "changed_files": len(changed_files),
        })
    else:
        # 全量重建 (有删除文件时也走全量)
        print("全量索引模式...")
        entries, file_count = load_sessions()
        if entries:
            build_index(entries)
        _file_mtime_cache = all_files
        return jsonify({
            "status": "ok",
            "mode": "full",
            "new_entries": len(entries),
            "total": index.ntotal if index else 0,
            "changed_files": len(changed_files),
            "deleted_files": len(deleted_files),
        })"""

assert old_reindex in content, "Could not find reindex block to patch"
content = content.replace(old_reindex, new_reindex)

# ====== MODIFY startup to load existing index with incremental logic ======
old_startup = """    if _os.path.exists(idx_file) and _os.path.exists(txt_file):
        print("加载已有索引...")
        index = faiss.read_index(idx_file)
        with open(txt_file) as f:
            text_store = json.load(f)
        print(f"已加载 {index.ntotal} 条，维度={index.d}")
    else:
        print("构建新索引...")
        entries, _ = load_sessions()
        build_index(entries)

    sessions_dir = os.path.expanduser("~/.openclaw/agents/main/sessions")
    if _os.path.exists(sessions_dir):
        for jf in glob.glob(f"{sessions_dir}/*.jsonl"):
            _file_mtime_cache[os.path.basename(jf)] = _os.path.getmtime(jf)"""

new_startup = """    if _os.path.exists(idx_file) and _os.path.exists(txt_file):
        print("加载已有索引...")
        index = faiss.read_index(idx_file)
        with open(txt_file) as f:
            text_store = json.load(f)
        # 优化5: 加载时重建 BM25 索引
        if text_store:
            _build_bm25(text_store)
        print(f"已加载 {index.ntotal} 条，维度={index.d}")
    else:
        print("构建新索引...")
        entries, _ = load_sessions()
        build_index(entries)

    sessions_dir = os.path.expanduser("~/.openclaw/agents/main/sessions")
    if _os.path.exists(sessions_dir):
        for jf in glob.glob(f"{sessions_dir}/*.jsonl"):
            _file_mtime_cache[os.path.basename(jf)] = _os.path.getmtime(jf)
        # 启动时增量检查：检查是否有新文件未在缓存中
        current_files = set(_os.path.basename(jf) for jf in glob.glob(f"{sessions_dir}/*.jsonl"))
        cached_files = set(_file_mtime_cache.keys())
        new_files = current_files - cached_files
        if new_files:
            print(f"启动时发现 {len(new_files)} 个新 session 文件，建议调用 /reindex?mode=incremental")"""

assert old_startup in content, "Could not find startup block to patch"
content = content.replace(old_startup, new_startup)

# Write patched file
with open(TARGET, "w") as f:
    f.write(content)

print("Patch applied successfully!")
print(f"Patched {TARGET}")
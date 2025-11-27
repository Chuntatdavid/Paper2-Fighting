# app.py   （修复版 + 功能更强）

import streamlit as st
import pandas as pd
import random

# ==================== 配置 ====================
st.set_page_config(page_title="保险中介人 Paper 2 刷题", layout="centered")

# ==================== 读取题目 ====================
import sys, os  # ← 如果文件最前面已经有这行就不用重复写

@st.cache_data
def load_questions():
    # 关键修复：打包成 exe 后也能找到 questions.csv
    csv_path = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(__file__)), "questions.csv")
    df = pd.read_csv(csv_path, encoding="utf-8")
    df = df.dropna(subset=["question"]).reset_index(drop=True)
    return df

df = load_questions()
TOTAL = len(df)
# ==================== 初始化 ====================
if "started" not in st.session_state:
    st.session_state.started = False
if "q_indices" not in st.session_state:
    st.session_state.q_indices = []
if "current_idx" not in st.session_state:   # 当前显示的是第几题（0 ~ len(q_indices)-1）
    st.session_state.current_idx = 0
if "user_answers" not in st.session_state:  # {真实行号: "A"/"B"/"C"/"D"}
    st.session_state.user_answers = {}
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# ==================== 开始界面 ====================
if not st.session_state.started:
    st.title("保险中介人 Paper 2 100题刷题神器")
    st.write(f"题库共 **{TOTAL}** 道题")

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        mode = st.radio(
            "选择做题模式",
            ["顺序做全部题", "随机抽题", "全部乱序"],
            horizontal=True
        )
    with col2:
        if mode == "随机抽题":
            custom_num = st.number_input(
                "想抽几道题？",
                min_value=1,
                max_value=TOTAL,
                value=50,
                step=5,
                help=f"题库共 {TOTAL} 题，可输入 1～{TOTAL} 之间的任意数字"
            )
        else:
            custom_num = None
    with col3:
        st.write("")
        st.write("")
        if st.button("开始测验", type="primary", use_container_width=True):
            if mode == "全部乱序":
                st.session_state.q_indices = random.sample(range(TOTAL), TOTAL)
            elif mode == "随机抽题":
                if custom_num >= TOTAL:
                    st.session_state.q_indices = list(range(TOTAL))
                else:
                    st.session_state.q_indices = random.sample(range(TOTAL), custom_num)
            else:  # 顺序做全部
                st.session_state.q_indices = list(range(TOTAL))

            st.session_state.current_idx = 0
            st.session_state.user_answers = {}
            st.session_state.submitted = False
            st.session_state.started = True
            st.rerun()

else:
    # ==================== 答题界面 ====================
    q_indices = st.session_state.q_indices
    n = len(q_indices)

    st.title("保险中介人 Paper 2 刷题")

    # ---------- 进度条 ----------
    answered = sum(1 for i in q_indices if i in st.session_state.user_answers)
    st.progress(answered / n)

    # ---------- 题号导航（独立容器，避免干扰）----------
    with st.container():
        cols = st.columns([1, 4, 1])
        with cols[0]:
            if st.button("上一题", disabled=st.session_state.current_idx == 0):
                st.session_state.current_idx -= 1
                st.rerun()
        with cols[1]:
            # 用一个纯展示的下拉框 + 手动“跳转”按钮，完全不干扰其他控件
            option_text = f"第 {st.session_state.current_idx+1} 题（原题号 {df.iloc[q_indices[st.session_state.current_idx]]['question_number']}）"
            selected = st.selectbox(
                "跳转到",
                options=[f"第 {i+1} 题（原题号 {df.iloc[q_indices[i]]['question_number']}）" for i in range(n)],
                index=st.session_state.current_idx,
                key="navigator",   # 唯一 key
                label_visibility="collapsed"
            )
        with cols[2]:
            if st.button("下一题", disabled=st.session_state.current_idx == n-1):
                st.session_state.current_idx += 1
                st.rerun()

    # 同步下拉框选择（用户在下拉框里选了别的题，点“跳转”按钮才跳）
    if st.button("跳转到所选题目", type="secondary"):
        selected_idx = int(selected.split("第 ")[1].split(" 题")[0]) - 1
        st.session_state.current_idx = selected_idx
        st.rerun()

    st.markdown("---")

    # ---------- 当前题目 ----------
    idx = st.session_state.current_idx
    real_idx = q_indices[idx]
    row = df.iloc[real_idx]

    st.markdown(f"### 第 {idx+1}/{n} 题　原题号：**{row['question_number']}**")
    st.write(row["question"])

    options = ["A", "B", "C", "D"]
    labels = [f"**{x}.** {row[f'option_{x.lower()}']}" for x in options]

    # 当前答案
    current = st.session_state.user_answers.get(real_idx, None)

    chosen = st.radio(
        "请选择你的答案：",
        options,
        format_func=lambda x: labels[options.index(x)],
        index=options.index(current) if current else None,
        key=f"answer_{real_idx}",   # 每题独立 key，互不干扰
        label_visibility="collapsed"
    )

    # 实时保存答案
    st.session_state.user_answers[real_idx] = chosen

    # ---------- 交卷按钮 ----------
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("交卷并查看成绩", type="primary", use_container_width=True):
            st.session_state.submitted = True
            st.rerun()

    # ==================== 交卷后显示成绩 ====================
    if st.session_state.submitted:
        st.markdown("---")
        st.balloons()

        correct = 0
        wrongs = []

        for real_idx in q_indices:
            user = st.session_state.user_answers.get(real_idx)
            answer = str(df.iloc[real_idx]["correct_answer"]).strip().upper()
            if user == answer:
                correct += 1
            else:
                wrongs.append(real_idx)

        rate = correct / n * 100

        st.success(f"### 测验完成！正确率 **{rate:.1f}%**（{correct}/{n}）")

        if wrongs:
            st.error(f"错题 {len(wrongs)} 道，已为你整理解析：")
            for real_idx in wrongs:
                r = df.iloc[real_idx]
                with st.expander(f"错题 {r['question_number']}　你的答案 {st.session_state.user_answers.get(real_idx)} → 正确 {r['correct_answer'].strip().upper()}"):
                    st.write(r["question"])
                    for opt in "ABCD":
                        st.write(f"{opt}. {r[f'option_{opt.lower()}']}")
                    st.markdown(f"**你的答案**：{st.session_state.user_answers.get(real_idx)} [错误]")
                    st.markdown(f"**正确答案**：{r['correct_answer'].strip().upper()} [正确]")
                    if pd.notna(r.get("explanation")) and r["explanation"].strip():
                        st.info(f"**解析**：{r['explanation']}")
                    else:
                        st.info("暂无解析")
        else:
            st.success("全对！太强了！")

        if st.button("再来一轮", type="primary"):
            st.session_state.clear()
            st.rerun()
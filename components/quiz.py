import streamlit as st
import streamlit.components.v1 as components
from utils.gpt import evaluate_answer_with_gpt
from utils.logger import setup_logger
import asyncio

# 問題数の制限を定数として定義
MAX_QUESTIONS = 15

def show_quiz_screen(df, logger=None):
    """クイズ画面を表示する関数"""
    if logger is None:
        logger = setup_logger(user_id=st.session_state.get('nickname'))
          
    st.title("🗽海外旅行の基礎知識Check🏝️")

    # セッション状態の初期化
    if 'answered_questions' not in st.session_state:
        st.session_state.answered_questions = set()
    if 'correct_answers' not in st.session_state:
        st.session_state.correct_answers = {}
    if 'answers_history' not in st.session_state:
        st.session_state.answers_history = {}
    if 'total_attempted' not in st.session_state:
        st.session_state.total_attempted = 0

    # 終了条件のチェック（total_attemptedベース）
    if st.session_state.total_attempted >= MAX_QUESTIONS:
        logger.info(f"ユーザー[{st.session_state.nickname}] - {MAX_QUESTIONS}問完了")
        st.session_state.quiz_results = {
            'total_questions': MAX_QUESTIONS,
            'correct_count': sum(1 for v in st.session_state.correct_answers.values() if v),
            'answers_history': st.session_state.answers_history
        }
        st.session_state.screen = 'result'
        st.rerun()
        return

    current_progress = st.session_state.total_attempted
    st.progress(current_progress / MAX_QUESTIONS)
    st.write(f"## 問題 {current_progress + 1} / {MAX_QUESTIONS}")
    current_question = st.session_state.question_index
    
    # 既に回答済みの問題をスキップ
    if current_question in st.session_state.answered_questions:
        st.session_state.question_index += 1
        if st.session_state.total_attempted >= MAX_QUESTIONS:
            st.session_state.screen = 'result'
        st.rerun()
        return
    
    # 問題の表示
    s_selected = df.loc[current_question]
    question = s_selected.loc['質問']
    options = [s_selected.loc[f'選択肢{opt}'] for opt in ['A', 'B', 'C']]

    logger.info(f"ユーザー[{st.session_state.nickname}] - 問題表示 - 問題番号: {current_question + 1}, 問題: {question}")

    st.markdown(f'## {question}')

    select_button = st.radio('回答を選択してください', options, index=None, horizontal=True)

    if st.button('回答を確定する'):
        if select_button is None:
            st.warning('回答を選択してください。')
            return
        
        handle_answer(select_button, question, options, current_question, logger)

    show_navigation_buttons(current_question, logger)

async def evaluate_answer_with_gpt_wrapper(question, options, user_answer):
    """GPT評価の呼び出しをラップする関数"""
    return await evaluate_answer_with_gpt(
        question=question,
        options=options,
        user_answer=user_answer
    )

def handle_answer(select_button, question, options, current_question, logger):
    """回答ハンドリング処理"""
    with st.spinner('GPT-4が回答を評価しています...'):
        gpt_response = asyncio.run(evaluate_answer_with_gpt_wrapper(
            question,
            options,
            select_button
        ))
    
    is_correct = "RESULT:[CORRECT]" in gpt_response
    
    # 回答結果の保存
    st.session_state.correct_answers[current_question] = is_correct
    st.session_state.answers_history[current_question] = {
        'question': question,
        'user_answer': select_button,
        'is_correct': is_correct,
        'explanation': gpt_response,
    }
    
    # ログにキャラクター情報を追加
    if is_correct:
        logger.info(f"ユーザー[{st.session_state.nickname}] - 正解 - 問題番号: {st.session_state.total_attempted + 1}, ユーザー回答: {select_button}")
    else:
        logger.info(f"ユーザー[{st.session_state.nickname}] - 不正解 - 問題番号: {st.session_state.total_attempted + 1}, ユーザー回答: {select_button}")
    
    show_answer_animation(is_correct)
    process_answer(is_correct, current_question, select_button, gpt_response, logger)

def show_answer_animation(is_correct):
    """正解・不正解のアニメーション表示"""
    if is_correct:
        st.markdown("""
            <style>
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(-5px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .result-container {
                    animation: fadeIn 0.4s ease-out;
                }
            </style>
            <div class='result-container' style='
                background-color: #d4edda;
                border-left: 4px solid #28a745;
                color: #155724;
                padding: 20px;
                border-radius: 8px;
                text-align: left;
                font-size: 16px;
                margin: 20px 0;
                position: relative;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            '>
                <div style='
                    display: flex;
                    align-items: center;
                    gap: 12px;
                '>
                    <span style='font-size: 24px;'>🎉</span>
                    <span style='font-weight: 600;'>正解です！</span>
                    <div style='
                        margin-left: auto;
                        background-color: #28a745;
                        color: white;
                        padding: 4px 12px;
                        border-radius: 12px;
                        font-size: 14px;
                        font-weight: 500;
                    '>
                        +1 point
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(-5px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .result-container {
                    animation: fadeIn 0.4s ease-out;
                }
            </style>
            <div class='result-container' style='
                background-color: #f8d7da;
                border-left: 4px solid #dc3545;
                color: #721c24;
                padding: 20px;
                border-radius: 8px;
                text-align: left;
                font-size: 16px;
                margin: 20px 0;
                position: relative;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            '>
                <div style='
                    display: flex;
                    align-items: center;
                    gap: 12px;
                '>
                    <span style='font-size: 24px;'>💫</span>
                    <span style='font-weight: 600;'>惜しいですね</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

def process_answer(is_correct, current_question, select_button, gpt_response, logger):
    """
    回答処理と表示を行う関数
    
    Parameters:
    -----------
    is_correct : bool
        回答が正解かどうか
    current_question : int
        現在の問題番号
    select_button : str
        ユーザーが選択した回答
    gpt_response : str
        GPTからのレスポンス
    logger : Logger
        ロギング用のロガーオブジェクト
    """
    # まず回答の正誤を処理
    if current_question not in st.session_state.answered_questions:
        if is_correct:
            logger.info(f"ユーザー[{st.session_state.nickname}] - 正解 - 問題番号: {st.session_state.total_attempted + 1}, ユーザー回答: {select_button}")
        else:
            logger.info(f"ユーザー[{st.session_state.nickname}] - 不正解 - 問題番号: {st.session_state.total_attempted + 1}, ユーザー回答: {select_button}")
        
        st.session_state.total_attempted += 1
        st.session_state.answered_questions.add(current_question)
    
    try:
        # GPTレスポンスから情報を抽出
        response_lines = gpt_response.strip().split('\n')
        user_answer = None
        correct_answer = None
        explanation = None
        
        for line in response_lines:
            line = line.strip()
            # RESULTの行をスキップ
            if line.startswith("RESULT:"):
                continue
                
            # コロンの位置を見つける
            colon_index = line.find(":")
            if colon_index != -1:
                key = line[:colon_index].strip()
                value = line[colon_index + 1:].strip()
                
                if "あなたの回答" in key:
                    user_answer = value
                elif "正解" in key:
                    correct_answer = value
                elif "解説" in key:
                    explanation = value

        # 値の検証とフォールバック
        if user_answer is None:
            logger.warning(f"ユーザー回答の取得に失敗: {gpt_response}")
            user_answer = select_button
        if correct_answer is None:
            logger.warning(f"正解の取得に失敗: {gpt_response}")
            correct_answer = "正解の取得に失敗しました"
        if explanation is None:
            logger.warning(f"解説の取得に失敗: {gpt_response}")
            explanation = gpt_response

        # デバッグ情報の表示（開発時のみ）
        if st.secrets.get("DEBUG_MODE", False):
            st.write("Debug - GPT Response:", gpt_response)
            st.write("Parsed values:", {
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "explanation": explanation[:100] + "..."
            })

        # スタイルの定義
        style = """
        <style>
        .explanation-box {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 16px;
            margin-top: 12px;
            background-color: #f8f9fa;
        }
        .answer-detail {
            display: flex;
            align-items: center;
            margin: 8px 0;
            font-size: 15px;
        }
        .answer-label {
            min-width: 120px;
            font-weight: 600;
            color: #555;
        }
        .answer-content {
            flex: 1;
            padding-left: 8px;
        }
        .explanation-text {
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid #e0e0e0;
            line-height: 1.6;
            color: #333;
        }
        </style>
        """

        # HTMLの生成
        html = f"""
        {style}
        <div class="explanation-box">
            <div class="answer-detail">
                <span class="answer-label">あなたの回答:</span>
                <span class="answer-content">{user_answer}</span>
            </div>
            <div class="answer-detail">
                <span class="answer-label">正解:</span>
                <span class="answer-content">{correct_answer}</span>
            </div>
            <div class="explanation-text">
                <strong>💡 解説:</strong><br>
                {explanation}
            </div>
        </div>
        """
        
        # 結果の表示
        st.markdown(html, unsafe_allow_html=True)
        
    except Exception as e:
        # エラーハンドリング
        logger.error(f"回答表示処理でエラーが発生: {str(e)}")
        st.error("回答の表示中にエラーが発生しました。")
        # エラー時はGPTレスポンスの生データを表示
        st.write("GPTレスポンス:", gpt_response)
        # エラーの詳細をログに記録
        logger.error(f"エラーの詳細: {str(e)}", exc_info=True)
    
def show_navigation_buttons(current_question, logger):
    """ナビゲーションボタンの表示"""
    # 解説との間にスペースを追加
    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.session_state.total_attempted >= MAX_QUESTIONS:
            if st.button('結果を見る🎖️', 
                        use_container_width=True, 
                        type="primary",
                        help="クイズが完了しました。結果を確認しましょう"):
                logger.info(f"ユーザー[{st.session_state.nickname}] - {MAX_QUESTIONS}問完了 - 結果画面へ遷移")
                st.session_state.screen = 'result'
                st.rerun()
        elif current_question in st.session_state.answered_questions:
            if st.button('次の問題へ ➡️', 
                        use_container_width=True,
                        type="secondary",
                        help="次の問題に進みます"):
                logger.info(f"ユーザー[{st.session_state.nickname}] - 次の問題へ進む - 現在の問題番号: {st.session_state.total_attempted + 1}")
                next_question = current_question
                while next_question in st.session_state.answered_questions:
                    next_question = (next_question + 1) % len(df)
                st.session_state.question_index = next_question
                st.rerun()
    
    # フッターのような余白を追加
    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)
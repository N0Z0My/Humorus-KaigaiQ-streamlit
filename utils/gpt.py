from openai import OpenAI
from utils.logger import setup_logger
import asyncio
from .config import SPREADSHEET_ID, OPENAI_API_KEY
import streamlit as st

# OpenAI クライアントの初期化
client = OpenAI(api_key=OPENAI_API_KEY)

# loggerの初期化
logger = setup_logger(spreadsheet_id=SPREADSHEET_ID, user_id="gpt")

# システムロールの定義
SYSTEM_ROLES = {
    "お笑い芸人": "あなたは海外旅行に詳しい、人気のお笑い芸人です。ユーモアのある解説を心がけてください。",
    "旅行ガイド": "あなたは20年以上の経験を持つベテランの旅行ガイドです。正確で詳細な情報を提供します。",
    "現地在住者": "あなたは海外在住10年以上の経験者です。現地の生活者視点での解説を提供します。",
    "歴史専門家": "あなたは各国の歴史と文化に詳しい専門家です。歴史的背景を交えた解説を提供します。",
    "グルメライター": "あなたは食文化に精通したグルメライターです。食に関する詳しい解説を提供します。"
}

def get_selected_roles(location="main"):
    """
    Streamlitの単一選択で回答者のキャラクターを1人選択
    
    Args:
        location (str): 'main' または 'sidebar' を指定してコンポーネントの表示位置を決定
    """
    # セレクトボックスの表示関数を決定
    if location == "sidebar":
        select_func = st.sidebar.selectbox  # multiselectからselectboxに変更
    else:
        select_func = st.selectbox
    
    # キャラクター選択UI（単一選択）
    selected_role = select_func(
        "回答者のキャラクターを選択してください",
        options=list(SYSTEM_ROLES.keys()),
        index=0,  # デフォルトで最初のキャラクター（お笑い芸人）を選択
        help="選択したキャラクターの視点で解説が得られます"
    )
    
    # 選択されたキャラクターをリストとして返す（既存コードとの互換性のため）
    return [selected_role]

def create_combined_system_role(selected_roles):
    """選択されたロールを組み合わせてシステムロールを作成"""
    if not selected_roles:
        return SYSTEM_ROLES["お笑い芸人"]  # デフォルトロール
    
    combined_role = "あなたは以下の特性を持つアドバイザーです：\n"
    for role in selected_roles:
        combined_role += f"- {SYSTEM_ROLES[role]}\n"
    return combined_role

async def evaluate_answer_with_gpt(question, options, user_answer, selected_roles=None):
    """GPTによる回答評価を行い、結果を返す"""
    if selected_roles is None:
        selected_roles = ["お笑い芸人"]
    
    system_role = create_combined_system_role(selected_roles)
    
    prompt = f"""
    問題: {question}
    選択肢: {options}
    ユーザーの回答: {user_answer}

    以下の手順でユーザーの回答を評価し、必ず指定された形式で回答してください：

    1. 問題文と選択肢から最も適切な選択肢を１つ選んでください。（この内容は出力しないでください）
    2. ユーザーの回答が最も適切な選択肢と一致するか評価してください。（この内容は出力しないでください）
    3. RESULT:[INCORRECT]の場合、ユーザーの回答にツッコミを入れ、正解の解説をしてください
    4. 以下のフォーマットで厳密に回答してください：

    RESULT:[CORRECT] または RESULT:[INCORRECT]
    あなたの回答: [ユーザーの回答]
    正解: [適切な選択肢]
    解説: [選択したキャラクターに応じた面白い解説]
    """

    try:
        logger.info(f"GPT評価開始 - 問題: {question}, ユーザー回答: {user_answer}")
        
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4",
            temperature=0.5,
            messages=[
                {"role": "system", "content": system_role},
                {"role": "user", "content": prompt}
            ]
        )
        
        gpt_response = response.choices[0].message.content
        logger.info(f"GPT評価完了 - 結果: {gpt_response}")
        
        return gpt_response

    except Exception as e:
        error_msg = f"エラーが発生しました: {str(e)}"
        logger.error(error_msg)
        return f"""
        RESULT:[INCORRECT]
        あなたの回答: {user_answer}
        正解: 評価中にエラーが発生しました
        解説: 申し訳ありません。回答の評価中にエラーが発生しました。もう一度お試しください。
        """
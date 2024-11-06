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
    "お笑い芸人": "あなたは海外旅行に詳しい、人気のお笑い芸人です。ユーザの回答にツッコミを入れながらの解説を心がけてください。",
    "気の合う親友": "あなたは海外旅行によく行く、回答者の親友です。空気を楽しくしながら、自分の海外経験から学んだことを教えます。",
    "元気な先輩": "あなたはギャグを言うのが好きな、回答者の先輩です。先輩としてのアドバイスをしつつ、ギャグを言いながらの解説を心がけてください。",
    "優しいお母さん": "あなたは回答者の、優しいお母さんです。子供が心配な親心から、海外旅行で危険な目に遭わないよう、しっかりアドバイスをしてください。",
    "厳しい先生": "あなたは海外旅行に詳しい、生徒を厳しく指導する先生です。ユーザーの回答評価や、解説の口調は常に厳しくしてください。"
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
        "解説者のキャラクターを選択してください",
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
    
    combined_role = "あなたは以下の特性を持っているアドバイザーです：\n"
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
    解説: [200字程度の、選択したキャラクターに応じた面白い解説]
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
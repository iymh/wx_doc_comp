# LOG
import logging
import json
logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)
logger = logging.getLogger("LOG")

# env
import os
from dotenv import load_dotenv
load_dotenv()

# ibm-watson
from ibm_watson import DiscoveryV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

# 環境変数から設定を読み込み
wd_key = os.getenv("WD_KEY", None)
wd_url = os.getenv("WD_URL", None)
prj_id = os.getenv("WD_PRJID", None)

authenticator = IAMAuthenticator(wd_key)
discovery = DiscoveryV2(
    version='2023-03-31',
    authenticator=authenticator
)
discovery.set_service_url(wd_url)

# prjs = discovery.list_projects().get_result()
# prj_ids = prjs['projects']
# print(f'ProjectID: {prj_ids}')

def check_required_params(params, required_params):
    """必須パラメータのチェックを行う共通関数"""
    for param in required_params:
        if param not in params or not params[param]:
            raise ValueError(f"{param} is required")

def call_getcollections():
    """コレクション一覧を取得する"""
    logger.info(f"call_getcollections")

    ret = discovery.list_collections(
        project_id=prj_id
    ).get_result()
    logger.info(ret)

    return ret

def call_wdsearch(params):
    """検索クエリを実行する"""
    logger.info(f"call_wdsearch: { params }")

    # 必須パラメータのチェック
    check_required_params(params, ["collection_ids", "count", "natural_language_query"])

    # 要件とカテゴリのみを検索対象にするためにpassagesを使用
    # paramsからpassagesを取得、なければデフォルト設定
    passages_config = params.get("passages")
    if not passages_config:
        passages_config = {
            "enabled": True,
            "fields": ["要件", "カテゴリ"],
            "find_answers": True,
            "per_document": True,
            "max_per_document": 1,
            "count": params["count"]
        }
    else:
        # countはparamsのcountに合わせる
        passages_config["count"] = params["count"]

    ret = discovery.query(
        project_id = prj_id,
        collection_ids = params["collection_ids"],
        count = params["count"],
        natural_language_query = params["natural_language_query"],
        passages = passages_config
    ).get_result()
    logger.info(ret)

    return ret

def call_wdautocomp(params):
    """オートコンプリートを取得する"""
    logger.info(f"call_wdautocomp: { params }")

    # 必須パラメータのチェック
    check_required_params(params, ["prefix", "count"])

    ret = discovery.get_autocompletion(
        project_id = prj_id,
        prefix = params["prefix"],
        count = params["count"]
    ).get_result()
    logger.info(ret)

    return ret

def call_listdocuments(params):
    """ドキュメント一覧を取得する"""
    logger.info(f"call_listdocuments: { params }")

    # 必須パラメータのチェック
    check_required_params(params, ["collection_id"])
    collection_id = params["collection_id"]
    
    # is_parentの確認
    is_parent = params.get("is_parent")
    logger.info(f"is_parent指定: {is_parent}")

    # APIパラメータの設定
    api_params = {
        'project_id': prj_id,
        'collection_id': collection_id
    }

    # オプションパラメータの追加
    option_map = {
        'count': 'count',
        'status': 'status',
        'has_notices': 'has_notices',
        'is_parent': 'is_parent', # IBM Cloud APIドキュメントどおりにis_parentを使用
        'return_fields': '_return'
    }
    
    for param, api_param in option_map.items():
        if param in params:
            api_params[api_param] = params[param]
            logger.info(f"オプションパラメータを設定: {param}={params[param]}")

    ret = discovery.list_documents(**api_params).get_result()
    logger.info(ret)

    return ret

def call_adddocument(params):
    """ドキュメントを追加する"""
    logger.info(f"call_adddocument 開始: { params }")

    try:
        # 必須パラメータのチェック
        logger.info("必須パラメータのチェック")
        check_required_params(params, ["collection_id"])
        collection_id = params["collection_id"]
        logger.info(f"collection_id: {collection_id}")

        # ファイル関連のパラメータチェック
        logger.info(f"file存在: {'file' in params}")
        logger.info(f"filename存在: {'filename' in params}")
        if 'file' not in params and 'filename' not in params:
            error_msg = "Either file or filename is required"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # APIパラメータの設定
        api_params = {
            'project_id': prj_id,
            'collection_id': collection_id
        }
        logger.info(f"初期APIパラメータ: {api_params}")
    
        # パラメータのチェックと設定
        if 'filename' not in params:
            error_msg = "filename is required"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        api_params['filename'] = params['filename']
        logger.info(f"filename パラメータを設定しました: {params['filename']}")
    
        # fileパラメータの処理
        if 'file' in params:
            api_params['file'] = params['file']
            logger.info("file パラメータを設定しました")
            
            # content_typeが指定されていればそれも設定
            if 'file_content_type' in params:
                api_params['file_content_type'] = params['file_content_type']
                logger.info(f"file_content_type を設定: {params['file_content_type']}")

        # オプションパラメータの追加
        for param in ['file_content_type', 'x_watson_discovery_force']:
            if param in params:
                api_params[param] = params[param]
                logger.info(f"{param} パラメータを設定: {params[param]}")

        logger.info(f"API呼び出し準備完了: {api_params}")
        ret = discovery.add_document(**api_params).get_result()
        logger.info(f"API呼び出し結果: {ret}")

        return ret
    except Exception as e:
        logger.error(f"call_adddocument エラー: {str(e)}")
        raise

def call_getdocument(params):
    """ドキュメントを取得する"""
    logger.info(f"call_getdocument: { params }")

    # 必須パラメータのチェック
    check_required_params(params, ["collection_id", "document_id"])
    collection_id = params["collection_id"]
    document_id = params["document_id"]

    # APIパラメータの設定
    api_params = {
        'project_id': prj_id,
        'collection_id': collection_id,
        'document_id': document_id
    }

    # オプションパラメータの追加
    if 'return_fields' in params:
        api_params['_return'] = params['return_fields']

    ret = discovery.get_document(**api_params).get_result()
    logger.info(ret)

    return ret

def call_updatedocument(params):
    """ドキュメントを更新する"""
    logger.info(f"call_updatedocument: { params }")

    # 必須パラメータのチェック
    check_required_params(params, ["collection_id", "document_id"])
    collection_id = params["collection_id"]
    document_id = params["document_id"]

    # APIパラメータの設定
    api_params = {
        'project_id': prj_id,
        'collection_id': collection_id,
        'document_id': document_id
    }

    # ファイルの設定
    if 'file' in params:
        api_params['file'] = params['file']
    elif 'filename' in params:
        api_params['filename'] = params['filename']

    # オプションパラメータの追加
    for param in ['file_content_type', 'metadata', 'x_watson_discovery_force']:
        if param in params:
            api_params[param] = params[param]

    ret = discovery.update_document(**api_params).get_result()
    logger.info(ret)

    return ret

def call_deletedocument(params):
    """ドキュメントを削除する"""
    logger.info(f"call_deletedocument: { params }")

    # 必須パラメータのチェック
    check_required_params(params, ["collection_id", "document_id"])
    collection_id = params["collection_id"]
    document_id = params["document_id"]

    # APIパラメータの設定
    api_params = {
        'project_id': prj_id,
        'collection_id': collection_id,
        'document_id': document_id
    }

    # オプションパラメータの追加
    if 'x_watson_discovery_force' in params:
        api_params['x_watson_discovery_force'] = params['x_watson_discovery_force']

    ret = discovery.delete_document(**api_params).get_result()
    logger.info(ret)

    return ret

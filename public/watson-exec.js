/**
 * @file watson-exec.js
 * API通信と関連ロジックをカプセル化したサービスモジュール。
 */

// --- ヘルパー関数 (ファイル内でのみ使用) ---

/**
 * APIを呼び出します。タイムアウト機能付き。
 * @param {string} method HTTPメソッド (GET, POST, etc.)
 * @param {string} apiUrl APIのエンドポイントURL
 * @param {object} params 送信するデータ
 * @param {number} [timeout=15000] タイムアウト時間 (ミリ秒)
 */
async function callApi(method, apiUrl, params, timeout = 15000) {
  // AbortControllerでタイムアウトを管理
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  const options = {
    method: method,
    headers: { "Content-Type": "application/json" },
    // fetchにsignalを渡して中断できるようにする
    signal: controller.signal 
  };
  
  if (params && method.toUpperCase() !== 'GET') {
    options.body = JSON.stringify(params);
  }

  try {
    const response = await fetch(apiUrl, options);
    if (!response.ok) throw new Error(`API call failed: ${response.status}`);
    const contentType = response.headers.get("content-type");
    return contentType?.includes("application/json") ? await response.json() : await response.text();
  } catch (error) {
    // タイムアウトによる中断の場合、エラー名が 'AbortError' になる
    if (error.name === 'AbortError') {
      console.error(`API通信タイムアウト (${apiUrl}): ${timeout}msを超えました`);
    } else {
      console.error(`API通信エラー (${apiUrl}):`, error);
    }
    return null;
  } finally {
    // 処理が完了したらタイマーを解除
    clearTimeout(timeoutId);
  }
}

function extractJson(text) {
  if (typeof text !== 'string') return null;
  const match = text.match(/```json([\s\S]*?)```/);
  return match ? match[1].trim() : null;
}

// --- メインクラス (外部から利用) ---

export class WatsonAPIs {
  /**
   * コンストラクタで全ての設定を初期化
   */
  constructor() {
    /**
     * APIとモデルに関する設定
     */
    this.config = {
      api: {
        baseUrl: "./",
        endpoints: {
          collections: "wdcols",
          search: "wdsearch",
          autocomp: "wdautocomp",
          generate: "gen"
        }
      },
      llm: {
        modelname: "meta-llama/llama-4-maverick-17b-128e-instruct-fp8"
        // modelname: "mistralai/mistral-medium-2505"
      }
    };

    /**
     * Watson Discoveryの検索パラメータの初期値
     */
    this.defaultDiscoveryParams = {
      collection_ids: [],
      filter: "",
      passages: { enabled: true, find_answers: true, per_document: true, fields: [] },
      count: 3,
      aggregation: "",
      _return: [],
    };

    /**
     * LLMに渡すプロンプトテンプレート
     */
    this.prompts = {
      system: `# 命令\nあなたは、与えられた"[要件]"の項目が、"[検索する機能]"と一致するかを判定するAIです。\n以下の"# ルール"と"# 出力形式"に厳密に従い、判定結果を生成してください。\n\n# ルール\n1.  "[要件]"に含まれるJSONオブジェクトを評価します。\n2.  **"judge"**の値は、評価対象オブジェクトの**"回答"キーの値（◯または×）を最優先**とし、そのまま反映させます。\n3.  **"score"**の値は、"要件"と"[検索する機能]"の**文言の一致度**に応じて、0点（全く不一致）から100点（完全一致）までの点数で設定します。\n4.  "reason"には、"judge"が[要件]の"回答"に基づいていること、および"score"が文言の一致度に基づいていることの両方を簡潔に記述します。\n5.  全ての評価結果を、単一のJSONにまとめてください。\n\n# 最重要ルール\n-   **出力は、後述の"# 出力形式"に合致する単一で有効なJSONのみとしてください。**\n-   **出力は \`\`\`json  から始まり \`\`\` で終わること。**\n\n`,
      search_item: "# 入力データ\n[検索する機能]: ",
      search_list: "[要件]:\n",
      result_title: `# 出力形式 (JSONの例)\n{\n  "judge": "（〇または×）",\n  "score": 100,\n  "reason": "（判定および点数の根拠）"\n}\n\n[判定結果]:\n`
    };
  }

  // --- クラスメソッド ---

  /**
   * Watson Discoveryのコレクションリストを取得します。
   */
  async fetchCollections() {
    const apiUrl = `${this.config.api.baseUrl}${this.config.api.endpoints.collections}`;
    const data = await callApi("GET", apiUrl);
    return data ? data.collections : null;
  }

  /**
   * Watson Discoveryに検索クエリを実行します。
   * @param {string} naturalLanguageQuery 自然言語の検索クエリ
   * @param {object} currentParams UIで設定された現在の検索パラメータ
   */
  async executeQuery(naturalLanguageQuery, currentParams) {
    const apiUrl = `${this.config.api.baseUrl}${this.config.api.endpoints.search}`;
    if (naturalLanguageQuery) naturalLanguageQuery = naturalLanguageQuery.replace(/\n/g, '');
    const queryParams = { ...currentParams, natural_language_query: naturalLanguageQuery };
    return await callApi("POST", apiUrl, queryParams);
  }

  /**
   * Watson Discoveryにサジェストワード取得を実行します。
   * @param {string} prefix 自然言語の検索クエリ
   * @param {object} currentParams UIで設定された現在の検索パラメータ
   */
  async executeAutocomp(prefix, currentParams) {
    const apiUrl = `${this.config.api.baseUrl}${this.config.api.endpoints.autocomp}`;
    const queryParams = { ...currentParams, prefix: prefix.replace(/\n/g, '') };
    return await callApi("POST", apiUrl, queryParams);
  }

  /**
   * AIによる判定処理をアイテムのリストに対して一括で実行します。
   * @param {Array<object>} items 判定対象のアイテム配列
   * @param {string} query 検索クエリ
   * @param {Function} onProgress 1件処理ごとの進捗通知コールバック
   */
  async processAIJudgements(items, query, onProgress) {
    for (let i = 0; i < items.length; i++) {
      let item = { ...items[i] };
      const wd_result = { 要件: item["要件"], 回答: item["回答"], システム名: item["システム名"], カテゴリ: item["カテゴリ"], id: item["id"], シート名: item["シート名"] };
      
      const llm_options = {
        modelname: this.config.llm.modelname,
        prompt: `${this.prompts.system}${this.prompts.search_item}${query}\n\n${this.prompts.search_list}\n${JSON.stringify(wd_result)}${this.prompts.result_title}`,
        decoding_method: "greedy",
        min_new_tokens: 10,
        max_new_tokens: 300,
        stop_sequences: []
      };
      
      const apiUrl = `${this.config.api.baseUrl}${this.config.api.endpoints.generate}`;
      const ret_text = await callApi("POST", apiUrl, llm_options);

      let ai_result = { judge: 'Error', reason: 'AIからの応答がありません', score: 0 };
      if (ret_text) {
        const extjson_str = extractJson(ret_text);
        if (extjson_str) {
          try {
            ai_result = JSON.parse(extjson_str);
          } catch (e) {
            console.error(e);
            ai_result = { judge: 'Error', reason: 'AIの応答形式が不正です', score: 0 };
          }
        }
      }
      item.ai_result = ai_result;

      if (typeof onProgress === 'function') {
        console.log(item);
        onProgress(i, item);
      }
    }
  }
}
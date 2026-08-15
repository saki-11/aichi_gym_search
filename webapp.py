from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi import Query
from fastapi.staticfiles import StaticFiles
from datetime import date

import search as search_module

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

# ============================================================
# トップページ
# ============================================================

@app.get("/", response_class=HTMLResponse)
def index():

    return """
    <!DOCTYPE html>
    <html lang="ja">

    <head>
        <meta charset="UTF-8">

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0"
        >

        <meta
            name="theme-color"
            content="#1976d2"
        >

        <link
            rel="manifest"
            href="/static/manifest.json"
        >

        <title>愛知県体育館空き検索</title>

        <style>

            * {
                box-sizing: border-box;
            }


            /* ==================================================
               全体
               ================================================== */

            body {
                font-family: sans-serif;

                margin: 0;
                padding: 15px;

                background: #f5f5f5;

                color: #333;
            }


            /* ==================================================
               タイトル
               ================================================== */

            h1 {
                font-size: 24px;

                margin: 5px 0 20px 0;

                text-align: center;
            }


            /* ==================================================
               フォーム
               ================================================== */

            .form {
                background: white;

                padding: 20px;

                border-radius: 12px;

                border: 1px solid #ccc;

                width: 100%;

                max-width: 500px;

                margin: 0 auto;
            }


            /* ==================================================
               ラベル
               ================================================== */

            .section-label {
                display: block;

                font-weight: bold;

                margin-bottom: 8px;
            }


            /* ==================================================
               セレクト・日付
               ================================================== */

            select,
            input[type="date"] {

                width: 100%;

                padding: 12px;

                font-size: 16px;

                margin-bottom: 20px;

                border: 1px solid #aaa;

                border-radius: 6px;

                background: white;
            }


            /* ==================================================
               曜日
               ================================================== */

            .weekday-group {

                display: grid;

                grid-template-columns:
                    repeat(4, 1fr);

                gap: 8px;

                margin-bottom: 12px;
            }


            .weekday {

                display: block;

                margin: 0;

                padding: 0;

                cursor: pointer;
            }


            .weekday input {

                position: absolute;

                opacity: 0;

                pointer-events: none;
            }


            .weekday span {

                display: flex;

                justify-content: center;

                align-items: center;

                min-height: 44px;

                border: 1px solid #ccc;

                border-radius: 8px;

                background: #fafafa;

                font-weight: bold;

                font-size: 15px;

                user-select: none;
            }


            .weekday input:checked + span {

                background: #1976d2;

                color: white;

                border-color: #1976d2;
            }


            /* ==================================================
               曜日一括選択
               ================================================== */

            .weekday-buttons {

                display: grid;

                grid-template-columns:
                    repeat(4, 1fr);

                gap: 8px;

                margin-bottom: 20px;
            }


            .weekday-button {

                width: 100%;

                padding: 10px 5px;

                margin: 0;

                font-size: 14px;

                font-weight: bold;

                border: 1px solid #aaa;

                border-radius: 8px;

                background: white;

                color: #333;

                cursor: pointer;
            }


            .weekday-button:active {

                opacity: 0.7;
            }


            /* ==================================================
               検索ボタン
               ================================================== */

            button.search-button {

                width: 100%;

                padding: 14px;

                font-size: 18px;

                font-weight: bold;

                cursor: pointer;

                border: none;

                border-radius: 8px;

                background: #1976d2;

                color: white;

                margin-top: 5px;
            }


            button.search-button:active {

                opacity: 0.8;
            }


            button.search-button:disabled {

                opacity: 0.7;

                cursor: default;
            }


            /* ==================================================
               検索中表示
               ================================================== */

            .loading-box {

                position: fixed;

                top: 0;
                left: 0;

                width: 100%;
                height: 100%;

                background: rgba(
                    255,
                    255,
                    255,
                    0.95
                );

                display: flex;

                flex-direction: column;

                justify-content: center;

                align-items: center;

                z-index: 9999;
            }


            .loading-title {

                font-size: 22px;

                font-weight: bold;

                margin-top: 20px;
            }


            .loading-text {

                margin-top: 10px;

                text-align: center;

                line-height: 1.6;
            }


            .spinner {

                width: 45px;

                height: 45px;

                border: 5px solid #ddd;

                border-top: 5px solid #1976d2;

                border-radius: 50%;

                animation:
                    spin 1s linear infinite;
            }


            @keyframes spin {

                0% {
                    transform: rotate(0deg);
                }

                100% {
                    transform: rotate(360deg);
                }

            }


            /* ==================================================
               小さいスマホ
               ================================================== */

            @media (max-width: 360px) {

                body {
                    padding: 10px;
                }


                .form {
                    padding: 15px;
                }


                h1 {
                    font-size: 21px;
                }


                .weekday-group {

                    grid-template-columns:
                        repeat(4, 1fr);

                    gap: 5px;
                }


                .weekday span {

                    min-height: 40px;

                    font-size: 13px;
                }


                .weekday-buttons {

                    gap: 5px;
                }


                .weekday-button {

                    font-size: 12px;

                    padding: 9px 3px;
                }

            }

        </style>

    </head>


    <body>


        <h1>
            愛知県体育館空き検索
        </h1>


        <div class="form">


            <form
                action="/search"
                method="get"
                id="search_form"
            >


                <!-- ==========================================
                     自治体
                     ========================================== -->

                <label
                    class="section-label"
                    for="city"
                >
                    自治体
                </label>


                <select
                    id="city"
                    name="city"
                >

                    <option value="KASUGAI">
                        春日井市
                    </option>

                    <option value="OWARIASAHI">
                        尾張旭市
                    </option>

                </select>


                <!-- ==========================================
                     検索日
                     ========================================== -->

                <label
                    class="section-label"
                    for="search_date"
                >
                    検索日
                </label>


                <input
                    type="date"
                    id="search_date"
                    name="search_date"
                    required
                >


                <!-- ==========================================
                     曜日
                     ========================================== -->

                <label class="section-label">
                    検索する曜日
                </label>


                <div class="weekday-group">


                    <label class="weekday">

                        <input
                            type="checkbox"
                            name="weekday"
                            value="0"
                        >

                        <span>月</span>

                    </label>


                    <label class="weekday">

                        <input
                            type="checkbox"
                            name="weekday"
                            value="1"
                        >

                        <span>火</span>

                    </label>


                    <label class="weekday">

                        <input
                            type="checkbox"
                            name="weekday"
                            value="2"
                        >

                        <span>水</span>

                    </label>


                    <label class="weekday">

                        <input
                            type="checkbox"
                            name="weekday"
                            value="3"
                        >

                        <span>木</span>

                    </label>


                    <label class="weekday">

                        <input
                            type="checkbox"
                            name="weekday"
                            value="4"
                        >

                        <span>金</span>

                    </label>


                    <label class="weekday">

                        <input
                            type="checkbox"
                            name="weekday"
                            value="5"
                        >

                        <span>土</span>

                    </label>


                    <label class="weekday">

                        <input
                            type="checkbox"
                            name="weekday"
                            value="6"
                        >

                        <span>日</span>

                    </label>


                    <label class="weekday">

                        <input
                            type="checkbox"
                            name="weekday"
                            value="7"
                        >

                        <span>祝</span>

                    </label>


                </div>


                <!-- ==========================================
                     曜日一括選択
                     ========================================== -->

                <div class="weekday-buttons">

                    <button
                        type="button"
                        class="weekday-button"
                        onclick="selectWeekday('weekday')"
                    >
                        平日
                    </button>


                    <button
                        type="button"
                        class="weekday-button"
                        onclick="selectWeekday('weekend')"
                    >
                        土日
                    </button>


                    <button
                        type="button"
                        class="weekday-button"
                        onclick="selectWeekday('all')"
                    >
                        すべて
                    </button>


                    <button
                        type="button"
                        class="weekday-button"
                        onclick="selectWeekday('clear')"
                    >
                        クリア
                    </button>

                </div>


                <!-- ==========================================
                     利用目的
                     ========================================== -->

                <label
                    class="section-label"
                    for="purpose"
                >
                    利用目的
                </label>


                <select
                    id="purpose"
                    name="purpose"
                >

                    <option value="volleyball">
                        バレーボール
                    </option>

                </select>


                <!-- ==========================================
                     検索ボタン
                     ========================================== -->

                <button
                    type="submit"
                    id="search_button"
                    class="search-button"
                >
                    検索
                </button>


            </form>


        </div>


        <!-- ==================================================
             検索中表示
             ================================================== -->

        <div
            id="loading"
            style="display: none;"
        >

            <div class="loading-box">

                <div class="spinner"></div>


                <div class="loading-title">
                    検索中です
                </div>


                <div class="loading-text">

                    空き状況を確認しています。<br>

                    しばらくお待ちください。

                </div>

            </div>

        </div>


        <!-- ==================================================
             JavaScript
             ================================================== -->

        <script>

            /*
             * 今日の日付を検索日の初期値にする
             */

            const today =
                new Date();


            const year =
                today.getFullYear();


            const month =
                String(
                    today.getMonth() + 1
                ).padStart(
                    2,
                    "0"
                );


            const day =
                String(
                    today.getDate()
                ).padStart(
                    2,
                    "0"
                );


            document.getElementById(
                "search_date"
            ).value =
                `${year}-${month}-${day}`;


            /*
             * 曜日チェックボックス
             */

            const weekdayCheckboxes =
                document.querySelectorAll(
                    'input[name="weekday"]'
                );


            /*
             * 曜日一括選択
             */

            function selectWeekday(type) {

                weekdayCheckboxes.forEach(
                    function (checkbox) {

                        const value =
                            Number(
                                checkbox.value
                            );


                        let checked =
                            false;


                        if (type === "weekday") {

                            /*
                             * 月～金
                             */

                            checked =
                                value >= 0 &&
                                value <= 4;

                        }


                        else if (
                            type === "weekend"
                        ) {

                            /*
                             * 土・日
                             */

                            checked =
                                value === 5 ||
                                value === 6;

                        }


                        else if (type === "all") {

                            /*
                             * 月～日・祝
                             */

                            checked = true;

                        }


                        else if (
                            type === "clear"
                        ) {

                            checked = false;

                        }


                        checkbox.checked =
                            checked;

                    }
                );

            }


            /*
             * 検索開始
             */

            const form =
                document.getElementById(
                    "search_form"
                );


            const loading =
                document.getElementById(
                    "loading"
                );


            const button =
                document.getElementById(
                    "search_button"
                );


            form.addEventListener(
                "submit",
                function () {

                    button.disabled =
                        true;


                    button.textContent =
                        "検索中...";


                    loading.style.display =
                        "block";

                }
            );

        </script>


    </body>

    </html>
    """

# ============================================================
# 検索
# ============================================================

# ============================================================
# 検索
# ============================================================

@app.get("/search", response_class=HTMLResponse)
def search(
    city: str = Query(default="KASUGAI"),
    search_date: date | None = Query(default=None),
    weekday: list[int] | None = Query(default=None)
):

    print()
    print("=" * 60)
    print("Webから検索処理を開始します")
    print("=" * 60)

    print(
        f"Webから受け取った自治体: {city}"
    )

    print(
        f"Webから受け取った検索日: {search_date}"
    )

    print(
        f"Webから受け取った曜日: {weekday}"
    )


    # ========================================================
    # 曜日設定を8要素に変換
    #
    # 月 火 水 木 金 土 日 祝
    # 0  0  0  0  0  0  0  0
    # ========================================================

    selected_week = [0] * 8

    if weekday:

        for day in weekday:

            index = int(day)

            if 0 <= index <= 7:
                selected_week[index] = 1

    print(
        f"Web側で作成した曜日設定: {selected_week}"
    )


    # ========================================================
    # 不正な自治体をチェック
    # ========================================================

    if city not in search_module.CITY_SETTINGS:

        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html lang="ja">

            <head>
                <meta charset="UTF-8">

                <meta
                    name="viewport"
                    content="width=device-width, initial-scale=1.0"
                >

                <title>エラー</title>

                <style>

                    body {
                        font-family: sans-serif;
                        margin: 0;
                        padding: 20px;
                        background: #f5f5f5;
                    }

                    .error {
                        background: white;
                        padding: 20px;
                        border-radius: 12px;
                        border: 1px solid #ccc;
                    }

                </style>

            </head>

            <body>

                <div class="error">

                    <h1>エラー</h1>

                    <p>
                        不正な自治体が指定されました。
                    </p>

                    <a href="/">
                        戻る
                    </a>

                </div>

            </body>

            </html>
            """,
            status_code=400
        )


    # ========================================================
    # 既存の検索プログラムを実行
    # ========================================================

    facilities = search_module.main(
        city,
        search_date,
        selected_week
    )


    print()
    print(
        f"Web側で受け取った施設数: {len(facilities)}"
    )


    # ========================================================
    # 空きがある施設だけ抽出
    # ========================================================

    available_facilities = []

    for facility_data in facilities:

        available_slots = facility_data.get(
            "available_slots",
            []
        )

        if available_slots:

            available_facilities.append(
                facility_data
            )


    # ========================================================
    # HTML開始
    # ========================================================

    html = """
    <!DOCTYPE html>
    <html lang="ja">

    <head>

        <meta charset="UTF-8">

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0"
        >

        <meta
            name="theme-color"
            content="#1976d2"
        >

        <title>検索結果</title>


        <style>

            * {
                box-sizing: border-box;
            }


            /* ==================================================
               全体
               ================================================== */

            body {

                font-family: sans-serif;

                margin: 0;

                padding: 12px;

                background: #f5f5f5;

                color: #333;

            }


            /* ==================================================
               タイトル
               ================================================== */

            h1 {

                font-size: 24px;

                margin: 5px 0 15px 0;

            }


            /* ==================================================
               検索概要
               ================================================== */

            .summary {

                background: white;

                border: 1px solid #ccc;

                border-radius: 12px;

                padding: 16px;

                margin-bottom: 15px;

            }


            .summary-title {

                font-size: 18px;

                font-weight: bold;

                margin-bottom: 12px;

            }


            .summary-condition {

                font-size: 15px;

                line-height: 1.7;

            }


            .summary-condition strong {

                font-size: 16px;

            }


            /* ==================================================
               空き施設数
               ================================================== */

            .available-count {

                margin-top: 14px;

                padding: 12px;

                border-radius: 8px;

                background: #e8f5e9;

                text-align: center;

            }


            .available-count-number {

                font-size: 28px;

                font-weight: bold;

            }


            .available-count-text {

                font-size: 15px;

                margin-left: 4px;

            }


            /* ==================================================
               施設カード
               ================================================== */

            .facility {

                background: white;

                border: 1px solid #ccc;

                border-radius: 12px;

                padding: 16px;

                margin-bottom: 15px;

            }


            /* ==================================================
               施設名
               ================================================== */

            .facility-name {

                font-size: 21px;

                font-weight: bold;

                line-height: 1.5;

                margin-bottom: 15px;

            }


            /* ==================================================
               日付
               ================================================== */

            .date {

                font-size: 18px;

                font-weight: bold;

                margin-top: 16px;

                margin-bottom: 8px;

                padding: 8px 10px;

                border-left: 5px solid #1976d2;

                background: #f1f6fb;

                border-radius: 4px;

            }


            /* ==================================================
               空き時間
               ================================================== */

            .slot {

                padding: 13px 12px;

                margin: 7px 0;

                border-radius: 8px;

                background: #e8f5e9;

                border: 1px solid #c8e6c9;

                font-size: 18px;

                font-weight: bold;

                text-align: center;

            }


            /* ==================================================
               空き時間ラベル
               ================================================== */

            .slot::before {

                content: "空き  ";

                font-size: 14px;

                font-weight: normal;

            }


            /* ==================================================
               空きなし
               ================================================== */

            .no-result {

                background: white;

                border: 1px solid #ccc;

                border-radius: 12px;

                padding: 25px 15px;

                text-align: center;

                font-size: 16px;

            }


            /* ==================================================
               戻る
               ================================================== */

            .back {

                margin-top: 20px;

                margin-bottom: 30px;

            }


            .back a {

                display: block;

                text-align: center;

                padding: 14px;

                background: white;

                border: 1px solid #aaa;

                border-radius: 8px;

                text-decoration: none;

                color: #333;

                font-size: 16px;

            }


            /* ==================================================
               小さいスマホ
               ================================================== */

            @media (max-width: 360px) {

                body {

                    padding: 10px;

                }


                h1 {

                    font-size: 21px;

                }


                .facility {

                    padding: 13px;

                }


                .facility-name {

                    font-size: 19px;

                }


                .date {

                    font-size: 16px;

                }


                .slot {

                    font-size: 17px;

                }

            }

        </style>

    </head>


    <body>

        <h1>
            検索結果
        </h1>
    """


    # ========================================================
    # 検索概要
    # ========================================================

    city_name = search_module.CITY_SETTINGS[city]["name"]


    html += f"""
        <div class="summary">

            <div class="summary-title">
                検索条件
            </div>


            <div class="summary-condition">

                自治体：
                <strong>
                    {city_name}
                </strong>

                <br>

                検索日：
                <strong>
                    {search_date}
                </strong>

                <br>

                利用目的：
                <strong>
                    バレーボール
                </strong>

            </div>


            <div class="available-count">

                <span class="available-count-number">
                    {len(available_facilities)}
                </span>

                <span class="available-count-text">
                    施設で空きあり
                </span>

            </div>

        </div>
    """


    # ========================================================
    # 空き施設を表示
    # ========================================================

    for facility_data in available_facilities:

        result = facility_data.get(
            "result",
            {}
        )


        facility_name = result.get(
            "facility",
            "施設名不明"
        )


        available_slots = facility_data.get(
            "available_slots",
            []
        )


        html += f"""
        <div class="facility">

            <div class="facility-name">
                {facility_name}
            </div>
        """


        current_date = None


        for slot in available_slots:

            slot_date = slot.get(
                "date"
            )


            date_text = slot.get(
                "date_text",
                slot_date
            )


            time = slot.get(
                "time",
                ""
            )


            # ==================================================
            # 日付が変わった場合
            # ==================================================

            if slot_date != current_date:

                if current_date is not None:

                    html += "</div>"


                html += f"""
                    <div class="date">

                        {date_text}

                    </div>

                    <div>
                """


                current_date = slot_date


            # ==================================================
            # 空き時間
            # ==================================================

            html += f"""
                <div class="slot">

                    {time}

                </div>
            """


        if current_date is not None:

            html += "</div>"


        html += """
        </div>
        """


    # ========================================================
    # 空きなし
    # ========================================================

    if not available_facilities:

        html += """
        <div class="no-result">

            空きのある施設はありませんでした。

        </div>
        """


    # ========================================================
    # 戻る
    # ========================================================

    html += """

        <div class="back">

            <a href="/">
                条件を変更して再検索
            </a>

        </div>


    </body>

    </html>

    """


    return html
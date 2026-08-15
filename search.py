import requests
from pathlib import Path
from bs4 import BeautifulSoup
import re
from datetime import datetime
from datetime import date
from dataclasses import dataclass

# ============================================================
# 基本設定
# ============================================================

BASE_URL = "https://www.e-shisetsu.e-aichi.jp/web"

TOP_URL = f"{BASE_URL}/index.jsp"

RESERVE_MENU_URL = (
    f"{BASE_URL}/rsvWTransInstSrchVacantAction.do"
)

PURPOSE_CATEGORY_URL = (
    f"{BASE_URL}/rsvWTransInstSrchPpsdAction.do"
)

PURPOSE_URL = (
    f"{BASE_URL}/rsvPrwia1000DispAction.do"
)

COMMUNITY_URL = (
    f"{BASE_URL}/rsvPrwia1000NextAction.do"
)

AREA_URL = (
    f"{BASE_URL}/rsvWTransInstSrchBuildAction.do"
)

BUILDING_URL = (
    f"{BASE_URL}/rsvWTransInstSrchInstAction.do"
)

FACILITY_URL = (
    f"{BASE_URL}/rsvWTransInstSrchDayWeekAction.do"
)

VACANT_URL = (
    f"{BASE_URL}/rsvWInstSrchVacantAction.do"
)


# ============================================================
# 検索対象自治体
# ============================================================

# ------------------------------------------------------------
# "OWARIASAHI" : 尾張旭市
# "KASUGAI"    : 春日井市
# ------------------------------------------------------------

TARGET_CITY = "OWARIASAHI"


CITY_SETTINGS = {

    "OWARIASAHI": {
        "name": "尾張旭市",
        "community_cd": "C8",
        "area_cd": "C801",
    },

    "KASUGAI": {
        "name": "春日井市",
        "community_cd": "A7",
        "area_cd": "A799",
    },
}


if TARGET_CITY not in CITY_SETTINGS:

    raise ValueError(
        f"不正なTARGET_CITY: {TARGET_CITY}"
    )


# ============================================================
# デフォルト検索条件
#
# これらはデフォルト値であり、検索処理中に変更しません。
# 実際の検索ごとの値は SearchContext に保持します。
# ============================================================

DEFAULT_SELECT_YY = "2026"
DEFAULT_SELECT_MM = "8"
DEFAULT_SELECT_DD = "13"

DEFAULT_SELECTED_WEEK = [
    0,
    0,
    0,
    0,
    0,
    1,
    1,
    1,
]

# ------------------------------------------------------------
# 利用目的
# ------------------------------------------------------------

PURPOSE_CATEGORY_CD = "1020"
PURPOSE_CD = "10200030"
PURPOSE_PURPOSE_CD = "1020"


# ------------------------------------------------------------
# 館
#
# 0 = 全施設
# ------------------------------------------------------------

BUILDING_CD = "0"


# ------------------------------------------------------------
# 最初の施設番号
#
# Web画面上の最初の施設が0。
# ------------------------------------------------------------

FIRST_FACILITY_INDEX = 0


# ============================================================
# 出力先
# ============================================================

OUTPUT_DIR = Path("step4")
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# 検索単位の状態
# ============================================================

@dataclass
class SearchContext:
    """1回の検索に必要な可変状態を保持する。"""

    session: requests.Session
    target_city: str
    city_name: str
    community_cd: str
    area_cd: str
    select_yy: str
    select_mm: str
    select_dd: str
    selected_week: list


# ============================================================
# 共通関数
# ============================================================

def make_disp_week():

    return [
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
    ]


def print_response_info(response):

    """
    print("STATUS:")
    print(response.status_code)

    print("URL:")
    print(response.url)

    print("Cookies:")
    print(session.cookies.get_dict())
    """

def save_response(response, filename):

    path = OUTPUT_DIR / filename

    response.encoding = "cp932"

    path.write_text(
        response.text,
        encoding="utf-8"
    )

    print(
        f"Response saved: {path}"
    )

    return path


def get_hidden_value(soup, name):

    element = soup.find(
        "input",
        {
            "type": "hidden",
            "name": name,
        }
    )

    if element is None:
        return ""

    return element.get(
        "value",
        ""
    )


# ============================================================
# form全体をPOSTデータ化
# ============================================================

def extract_form_data(soup):
    """
    現在表示されているHTMLのformから、
    submit対象となるinput/select/textareaを
    可能な限りそのまま抽出する。

    次施設ボタンはJavaScriptでform.submit()しているため、
    手動で必要項目だけを再構成するのではなく、
    現在画面のform状態をそのまま引き継ぐ。
    """

    form = None

    # --------------------------------------------------------
    # VACANT画面のformを優先して探す
    # --------------------------------------------------------

    for candidate in soup.find_all("form"):

        action = candidate.get(
            "action",
            ""
        )

        if (
            "rsvWInstSrchVacantAction.do"
            in action
        ):

            form = candidate
            break


    # --------------------------------------------------------
    # 見つからなければ最初のform
    # --------------------------------------------------------

    if form is None:

        form = soup.find("form")


    if form is None:

        raise RuntimeError(
            "HTML内にformが見つかりません。"
        )


    data = []


    # ========================================================
    # input
    # ========================================================

    for element in form.find_all("input"):

        name = element.get("name")

        if not name:
            continue

        input_type = (
            element.get("type", "text")
            .lower()
        )

        # ----------------------------------------------------
        # submit/button/image は通常のform.submit()では
        # submitされないため除外
        # ----------------------------------------------------

        if input_type in (
            "submit",
            "button",
            "image",
            "reset",
        ):

            continue


        # ----------------------------------------------------
        # checkbox / radio
        # ----------------------------------------------------

        if input_type in (
            "checkbox",
            "radio",
        ):

            if not element.has_attr("checked"):

                continue


        value = element.get(
            "value",
            ""
        )

        data.append(
            (
                name,
                value
            )
        )


    # ========================================================
    # select
    # ========================================================

    for select in form.find_all("select"):

        name = select.get("name")

        if not name:
            continue


        options = select.find_all(
            "option"
        )

        selected_options = [
            option
            for option in options
            if option.has_attr("selected")
        ]


        if not selected_options and options:

            selected_options = [
                options[0]
            ]


        for option in selected_options:

            data.append(
                (
                    name,
                    option.get(
                        "value",
                        ""
                    )
                )
            )


    # ========================================================
    # textarea
    # ========================================================

    for textarea in form.find_all(
        "textarea"
    ):

        name = textarea.get("name")

        if not name:
            continue

        data.append(
            (
                name,
                textarea.get_text()
            )
        )


    return data


# ============================================================
# POSTデータの値を上書き
# ============================================================

def set_post_value(data, name, value):
    """
    formから取得したname/valueリストの、
    指定nameをすべて削除してから末尾に追加する。

    同名hiddenが複数存在する場合にも対応する。
    """

    data = [
        (
            current_name,
            current_value
        )
        for current_name, current_value in data
        if current_name != name
    ]

    data.append(
        (
            name,
            str(value)
        )
    )

    return data


# ============================================================
# POSTデータ表示
# ============================================================

def print_post_data(data):

    print()
    """
    print("POST DATA:")

    for name, value in data:

        print(
            f"  {name} = {value}"
        )
    """

# ============================================================
# 全角数字 → 半角数字
# ============================================================

def normalize_digits(text):

    if text is None:
        return ""

    return text.translate(
        str.maketrans(
            "０１２３４５６７８９",
            "0123456789"
        )
    )


# ============================================================
# 時刻文字列を正規化
# ============================================================

def normalize_time_range(text):

    if not text:
        return None, None

    text = normalize_digits(text)

    text = re.sub(
        r"\s+",
        "",
        text
    )

    text = re.sub(
        r"<[^>]+>",
        "",
        text
    )


    match = re.search(
        r"(\d{1,2})時(\d{1,2})分?～"
        r"(\d{1,2})時(\d{1,2})分?",
        text
    )

    if match:

        start_hour = int(match.group(1))
        start_min = int(match.group(2))

        end_hour = int(match.group(3))
        end_min = int(match.group(4))

        return (
            f"{start_hour:02d}:{start_min:02d}",
            f"{end_hour:02d}:{end_min:02d}",
        )


    match = re.search(
        r"(\d{1,2})時～(\d{1,2})時",
        text
    )

    if match:

        start_hour = int(match.group(1))
        end_hour = int(match.group(2))

        return (
            f"{start_hour:02d}:00",
            f"{end_hour:02d}:00",
        )


    return None, None


# ============================================================
# 時間範囲テキスト抽出
# ============================================================

def extract_time_range_from_cell_text(text):

    if not text:
        return None, None

    normalized = normalize_digits(text)

    normalized = re.sub(
        r"\s+",
        "",
        normalized
    )


    match = re.search(
        r"(\d{1,2})時(\d{1,2})分?～"
        r"(\d{1,2})時(\d{1,2})分?",
        normalized
    )

    if match:

        return (
            f"{int(match.group(1)):02d}:"
            f"{int(match.group(2)):02d}",

            f"{int(match.group(3)):02d}:"
            f"{int(match.group(4)):02d}",
        )


    match = re.search(
        r"(\d{1,2})時～(\d{1,2})時",
        normalized
    )

    if match:

        return (
            f"{int(match.group(1)):02d}:00",
            f"{int(match.group(2)):02d}:00",
        )


    return None, None


# ============================================================
# 空き状況HTML解析
# ============================================================

def parse_vacant_result(html_source, fallback_year=None):

    if isinstance(html_source, Path):

        html = html_source.read_text(
            encoding="utf-8"
        )

    elif isinstance(html_source, str):

        html = html_source

    else:

        raise TypeError(
            "html_source は Path または str"
        )


    soup = BeautifulSoup(
        html,
        "html.parser"
    )


    table = soup.select_one(
        "table.rsvakitable"
    )

    if table is None:

        return {
            "facility": None,
            "year": None,
            "dates": [],
            "times": [],
            "results": [],
        }


    # ========================================================
    # 施設名
    # ========================================================

    facility = None

    caption = table.find(
        "caption"
    )

    if caption is not None:

        caption_copy = BeautifulSoup(
            str(caption),
            "html.parser"
        )

        for link in caption_copy.find_all(
            "a"
        ):

            link.replace_with(
                link.get_text(
                    " ",
                    strip=True
                )
            )

        facility = caption_copy.get_text(
            " ",
            strip=True
        )

        facility = re.sub(
            r"\s*空き状況\s*$",
            "",
            facility
        ).strip()

        facility = re.sub(
            r"\(新しいウィンドウで開きます\)",
            "",
            facility
        ).strip()


    if not facility:

        facility_area = soup.select_one(
            "#rsvaki2"
        )

        if facility_area is not None:

            facility = facility_area.get_text(
                " ",
                strip=True
            )


    # ========================================================
    # 年
    # ========================================================

    year = None

    year_element = soup.find(
        id="rsvyear"
    )

    if year_element is not None:

        year_text = year_element.get_text(
            " ",
            strip=True
        )

        year_match = re.search(
            r"(\d{4})年",
            year_text
        )

        if year_match:

            year = int(
                year_match.group(1)
            )


    if year is None:

        year_match = re.search(
            r"(\d{4})年",
            soup.get_text(
                " ",
                strip=True
            )
        )

        if year_match:

            year = int(
                year_match.group(1)
            )


    if year is None and fallback_year is not None:

        try:
            year = int(fallback_year)
        except (TypeError, ValueError):
            year = None


    # ========================================================
    # 日付
    # ========================================================

    dates = []

    for i in range(7):

        th = soup.find(
            "th",
            id=f"rsvday{i}"
        )

        if th is None:
            continue

        text = th.get_text(
            " ",
            strip=True
        )

        match = re.search(
            r"(\d{1,2})月(\d{1,2})日",
            text
        )

        if match is None:
            continue

        month = int(match.group(1))
        day = int(match.group(2))

        iso_date = None

        if year is not None:

            iso_date = (
                f"{year:04d}-"
                f"{month:02d}-"
                f"{day:02d}"
            )

        dates.append({
            "index": i,
            "month": month,
            "day": day,
            "text": text,
            "date": iso_date,
        })


    if not dates:

        for th in table.find_all("th"):

            text = th.get_text(
                " ",
                strip=True
            )

            match = re.search(
                r"(\d{1,2})月(\d{1,2})日",
                text
            )

            if match is None:
                continue

            month = int(match.group(1))
            day = int(match.group(2))

            iso_date = None

            if year is not None:

                iso_date = (
                    f"{year:04d}-"
                    f"{month:02d}-"
                    f"{day:02d}"
                )

            dates.append({
                "index": len(dates),
                "month": month,
                "day": day,
                "text": text,
                "date": iso_date,
            })

            if len(dates) >= 7:
                break


    # ========================================================
    # 状態判定
    # ========================================================

    def detect_status(img):

        if img is None:
            return "不明"

        alt = (
            img.get("alt") or ""
        ).strip()

        image = (
            img.get("src") or ""
        ).strip()


        alt_statuses = [
            "予約あり",
            "空き",
            "休館日",
            "保守日",
            "受付期間外",
            "一般開放",
            "貸出時間なし",
        ]

        for status in alt_statuses:

            if status in alt:
                return status


        image_lower = image.lower()

        if "finishs" in image_lower:
            return "予約あり"

        elif "emptybs" in image_lower:
            return "空き"

        elif "closes" in image_lower:
            return "休館日"

        elif "keeps" in image_lower:
            return "保守日"

        elif "kikangais" in image_lower:
            return "受付期間外"

        elif "lw_3_" in image_lower:
            return "一般開放"

        elif "600" in image_lower:
            return "貸出時間なし"


        return "不明"


    # ========================================================
    # 時間帯
    # ========================================================

    times = []
    results = []


    has_tzone = (
        table.find(
            "th",
            id=re.compile(r"^tzone\d+$")
        )
        is not None
    )


    # ========================================================
    # 方式1
    # ========================================================

    if has_tzone:

        rows = table.find_all("tr")

        for row_index, row in enumerate(rows):

            th = row.find(
                "th",
                id=f"tzone{row_index}"
            )

            if th is None:

                for candidate in row.find_all("th"):

                    text = candidate.get_text(
                        " ",
                        strip=True
                    )

                    normalized = normalize_digits(
                        text
                    )

                    if re.search(
                        r"[0-9]+時",
                        normalized
                    ):

                        th = candidate
                        break


            if th is None:
                continue


            time_zone = th.get_text(
                " ",
                strip=True
            )

            normalized_time = normalize_digits(
                time_zone
            )

            time_match = re.search(
                r"(\d{1,2})時",
                normalized_time
            )

            if time_match:

                hour = int(
                    time_match.group(1)
                )

                time_value = (
                    f"{hour:02d}:00"
                )

            else:

                time_value = time_zone


            times.append(
                time_value
            )


            cells = row.find_all(
                "td"
            )


            for day_index in range(7):

                if day_index < len(dates):

                    date_info = dates[
                        day_index
                    ]

                else:

                    date_info = {
                        "index": day_index,
                        "month": None,
                        "day": None,
                        "text": "",
                        "date": None,
                    }


                if day_index >= len(cells):

                    results.append({
                        "date": date_info["date"],
                        "date_text": date_info["text"],
                        "time": time_value,
                        "status": "不明",
                        "cell_id": None,
                        "alt": "",
                        "image": "",
                    })

                    continue


                cell = cells[
                    day_index
                ]

                img = cell.find(
                    "img"
                )


                if img is None:

                    results.append({
                        "date": date_info["date"],
                        "date_text": date_info["text"],
                        "time": time_value,
                        "status": "不明",
                        "cell_id": None,
                        "alt": "",
                        "image": "",
                    })

                    continue


                results.append({
                    "date": date_info["date"],
                    "date_text": date_info["text"],
                    "time": time_value,
                    "status": detect_status(img),
                    "cell_id": img.get("id"),
                    "alt": (
                        img.get("alt") or ""
                    ).strip(),
                    "image": (
                        img.get("src") or ""
                    ).strip(),
                })


    # ========================================================
    # 方式2
    # ========================================================

    else:

        date_cells = []

        for day_index in range(7):

            cell = table.find(
                "td",
                attrs={
                    "headers": f"rsvday{day_index}"
                }
            )

            if cell is None:
                continue

            date_cells.append(
                (
                    day_index,
                    cell
                )
            )


        if not date_cells:

            rows = table.find_all(
                "tr"
            )

            for row in rows:

                cells = row.find_all(
                    "td"
                )

                if len(cells) < len(dates):
                    continue

                for day_index, cell in enumerate(
                    cells[:7]
                ):

                    date_cells.append(
                        (
                            day_index,
                            cell
                        )
                    )

                break


        for day_index, cell in date_cells:

            if day_index >= len(dates):
                continue

            date_info = dates[
                day_index
            ]

            images = cell.find_all(
                "img"
            )


            for image_index, img in enumerate(
                images
            ):

                status = detect_status(
                    img
                )

                fragment_parts = []

                current = img.next_sibling

                while current is not None:

                    if getattr(
                        current,
                        "name",
                        None
                    ) == "img":

                        break

                    if (
                        getattr(
                            current,
                            "name",
                            None
                        ) == "div"
                        and
                        "csshr" in (
                            current.get(
                                "class",
                                []
                            )
                        )
                    ):

                        break

                    if hasattr(
                        current,
                        "get_text"
                    ):

                        fragment_parts.append(
                            current.get_text(
                                " ",
                                strip=True
                            )
                        )

                    else:

                        fragment_parts.append(
                            str(current)
                        )

                    current = current.next_sibling


                fragment_text = " ".join(
                    fragment_parts
                )


                start_time, end_time = (
                    extract_time_range_from_cell_text(
                        fragment_text
                    )
                )


                if start_time is None:

                    cell_text = cell.get_text(
                        " ",
                        strip=True
                    )

                    all_ranges = re.findall(
                        r"(\d{1,2})時(\d{1,2})分?"
                        r"～"
                        r"(\d{1,2})時(\d{1,2})分?",
                        normalize_digits(
                            cell_text
                        )
                    )

                    if image_index < len(
                        all_ranges
                    ):

                        r = all_ranges[
                            image_index
                        ]

                        start_time = (
                            f"{int(r[0]):02d}:"
                            f"{int(r[1]):02d}"
                        )

                        end_time = (
                            f"{int(r[2]):02d}:"
                            f"{int(r[3]):02d}"
                        )


                if (
                    start_time is not None
                    and
                    end_time is not None
                ):

                    time_value = (
                        f"{start_time}-{end_time}"
                    )

                else:

                    time_value = ""


                if time_value:

                    times.append(
                        time_value
                    )


                results.append({
                    "date": date_info["date"],
                    "date_text": date_info["text"],
                    "time": time_value,
                    "status": status,
                    "cell_id": img.get("id"),
                    "alt": (
                        img.get("alt") or ""
                    ).strip(),
                    "image": (
                        img.get("src") or ""
                    ).strip(),
                })


    times = list(
        dict.fromkeys(
            times
        )
    )


    return {
        "facility": facility,
        "year": year,
        "dates": dates,
        "times": times,
        "results": results,
    }


# ============================================================
# 空き時間だけ取得
# ============================================================

def get_available_slots(result):

    return [
        item
        for item in result.get(
            "results",
            []
        )
        if item.get("status") == "空き"
    ]


# ============================================================
# 検索期間
# ============================================================

def get_search_period(result):

    dates = result.get(
        "dates",
        []
    )

    if not dates:
        return None, None

    return (
        dates[0].get("date"),
        dates[-1].get("date")
    )


# ============================================================
# 曜日
# ============================================================

def get_weekday_text(date_string):

    if not date_string:
        return ""

    try:

        date_value = datetime.strptime(
            date_string,
            "%Y-%m-%d"
        )

    except ValueError:

        return ""

    weekdays = [
        "月",
        "火",
        "水",
        "木",
        "金",
        "土",
        "日",
    ]

    return weekdays[
        date_value.weekday()
    ]


# ============================================================
# 空き時間一覧表示
# ============================================================

def print_available_summary(ctx, facilities):

    print()
    print("=" * 70)
    print(
        f"空き時間一覧 "
        f"({ctx.city_name})"
    )
    print("=" * 70)


    if not facilities:

        print(
            "施設情報がありません。"
        )

        return


    first_period = None
    last_period = None


    for facility in facilities:

        result = facility["result"]

        first_date, last_date = (
            get_search_period(
                result
            )
        )

        if first_date:

            if (
                first_period is None
                or first_date < first_period
            ):

                first_period = first_date


        if last_date:

            if (
                last_period is None
                or last_date > last_period
            ):

                last_period = last_date


    print()

    if first_period and last_period:

        print(
            f"検索期間: "
            f"{first_period} ～ "
            f"{last_period}"
        )

    else:

        print(
            "検索期間: 不明"
        )


    total_available = 0


    for facility in facilities:

        index = facility["index"]

        result = facility["result"]

        facility_name = (
            result.get("facility")
            or f"施設 {index}"
        )

        available_slots = (
            facility["available_slots"]
        )


        print()
        print(
            f"[施設 {index}] "
            f"{facility_name}"
        )


        if not available_slots:

            print(
                "  空きなし"
            )

            continue


        sorted_slots = sorted(
            available_slots,
            key=lambda item: (
                item.get("date") or "",
                item.get("time") or "",
            )
        )


        for item in sorted_slots:

            date = item.get(
                "date"
            )

            time = item.get(
                "time"
            )

            weekday = get_weekday_text(
                date
            )

            if date and weekday:

                print(
                    f"  {date}"
                    f"({weekday}) "
                    f"{time}"
                )

            elif date:

                print(
                    f"  {date} "
                    f"{time}"
                )

            else:

                print(
                    f"  {item.get('date_text', '')} "
                    f"{time}"
                )


            total_available += 1


    print()
    print("-" * 70)

    print(
        f"空き時間合計: "
        f"{total_available}件"
    )

    print("=" * 70)


# ============================================================
# STEP 1
# ============================================================

def step1_top(ctx):

    print()
    print("=" * 60)
    print("STEP 1: TOP")
    print("=" * 60)

    response = ctx.session.get(
        TOP_URL
    )

    print_response_info(
        response
    )

    response.raise_for_status()

    save_response(
        response,
        "01_top.html"
    )


# ============================================================
# STEP 2
# ============================================================

def step2_reserve_menu(ctx):

    print()
    print("=" * 60)
    print("STEP 2: 予約")
    print("=" * 60)

    payload = {
        "displayNo": "prwaa1000",
        "selectMenu": "1",

        "selectAreaCd": "",
        "selectBldCd": "",
        "selectPpsdCd": "0",
        "selectPpsCd": "0",
        "selectPpsPpsdCd": "0",
        "selectInstNo": "0",

        "dispWeekNum": "0",
        "dispWeek": make_disp_week(),

        "submmitMode": "0",
        "conditionMode": "2",
        "transVacantMode": "0",

        "dispSelectInstBldCd": "",
        "dispSelectInstCd": "",

        "selectCommunityManageCd": "",
        "selectCommunityPlaceCd": "",

        "processMode": "0",
    }

    response = ctx.session.post(
        RESERVE_MENU_URL,
        data=payload,
    )

    print_response_info(
        response
    )

    response.raise_for_status()

    save_response(
        response,
        "02_reserve_menu.html"
    )


# ============================================================
# STEP 3
# ============================================================

def step3_purpose_category(ctx):

    print()
    print("=" * 60)
    print("STEP 3: 利用目的分類")
    print("=" * 60)

    payload = {
        "displayNo": "prwaa1000",

        "selectAreaCd": "",
        "selectBldCd": "0",

        "selectPpsdCd": "0",
        "selectPpsCd": "0",
        "selectPpsPpsdCd": "0",

        "selectInstNo": "0",

        "dispWeekNum": "0",
        "dispWeek": make_disp_week(),

        "submmitMode": "0",
        "transVacantMode": "0",
        "conditionMode": "2",

        "dispSelectInstBldCd": "",
        "dispSelectInstCd": "",

        "selectCommunityManageCd": "0",
        "selectCommunityPlaceCd": "0",

        "productMode": "3",
        "areaMode": "2",

        "processMode": "0",
    }

    response = ctx.session.post(
        PURPOSE_CATEGORY_URL,
        data=payload,
    )

    print_response_info(
        response
    )

    response.raise_for_status()

    save_response(
        response,
        "03_purpose_category.html"
    )


# ============================================================
# STEP 4
# ============================================================

def step4_sports_category(ctx):

    print()
    print("=" * 60)
    print("STEP 4: 体育／バレー・バスケ")
    print("=" * 60)

    payload = {
        "displayNo": "prwbb5000",

        "selectAreaCd": "",
        "selectBldCd": "0",

        "selectPpsdCd": PURPOSE_CATEGORY_CD,
        "selectPpsCd": "0",
        "selectPpsPpsdCd": "0",

        "selectInstNo": "0",

        "dispWeekNum": "0",
        "dispWeek": make_disp_week(),

        "submmitMode": "0",
        "transVacantMode": "0",
        "conditionMode": "2",

        "dispSelectInstBldCd": "",
        "dispSelectInstCd": "",

        "selectCommunityManageCd": "0",
        "selectCommunityPlaceCd": "0",

        "productMode": "3",
        "areaMode": "2",

        "processMode": "0",
    }

    response = ctx.session.post(
        PURPOSE_CATEGORY_URL,
        data=payload,
    )

    print_response_info(
        response
    )

    response.raise_for_status()

    save_response(
        response,
        "04_sports_category.html"
    )


# ============================================================
# STEP 5
# ============================================================

def step5_volleyball(ctx):

    print()
    print("=" * 60)
    print("STEP 5: バレーボール")
    print("=" * 60)

    payload = {
        "displayNo": "prwbb6000",
        "selectMenu": "1",

        "selectAreaCd": "",
        "selectBldCd": "0",

        "selectPpsdCd": PURPOSE_CATEGORY_CD,
        "selectPpsCd": PURPOSE_CD,
        "selectPpsPpsdCd": PURPOSE_PURPOSE_CD,

        "selectInstNo": "0",

        "dispWeekNum": "0",
        "dispWeek": make_disp_week(),

        "submmitMode": "1",
        "transVacantMode": "7",
        "conditionMode": "2",

        "dispSelectInstBldCd": "",
        "dispSelectInstCd": "",

        "selectCommunityManageCd": "",
        "selectCommunityPlaceCd": "0",

        "productMode": "3",
        "areaMode": "2",

        "processMode": "4",
    }

    response = ctx.session.post(
        PURPOSE_URL,
        data=payload
    )

    print_response_info(
        response
    )

    response.raise_for_status()

    save_response(
        response,
        "05_volleyball.html"
    )


# ============================================================
# STEP 6
# ============================================================

def step6_community(ctx):

    print()
    print("=" * 60)
    print(
        f"STEP 6: 自治体 - {ctx.city_name}"
    )
    print("=" * 60)

    print(
        f"ctx.community_cd = {ctx.community_cd}"
    )

    payload = {
        "selectMenu": "1",
        "selectedCommunityCd": ctx.community_cd,
        "displayNo": "prwia1000",
        "processMode": "4",
    }

    response = ctx.session.post(
        COMMUNITY_URL,
        data=payload
    )

    print_response_info(
        response
    )

    response.raise_for_status()

    save_response(
        response,
        f"06_{ctx.target_city.lower()}.html"
    )


# ============================================================
# STEP 7
# ============================================================

def step7_area(ctx):

    print()
    print("=" * 60)
    print(
        f"STEP 7: 地域 - {ctx.city_name}"
    )
    print("=" * 60)

    print(
        f"ctx.area_cd = {ctx.area_cd}"
    )

    payload = {
        "displayNo": "prwbb1000",
        "selectMenu": "1",

        "selectAreaCd": ctx.area_cd,
        "selectBldCd": "0",

        "selectPpsdCd": PURPOSE_CATEGORY_CD,
        "selectPpsCd": PURPOSE_CD,
        "selectPpsPpsdCd": PURPOSE_PURPOSE_CD,

        "favSelectPpsdCd": PURPOSE_CATEGORY_CD,

        "selectInstNo": "0",

        "dispWeekNum": "0",
        "dispWeek": make_disp_week(),

        "submmitMode": "1",
        "transVacantMode": "7",
        "conditionMode": "2",

        "dispSelectInstBldCd": "",
        "dispSelectInstCd": "",

        "selectCommunityManageCd": ctx.community_cd,
        "selectCommunityPlaceCd": "0",

        "productMode": "3",
        "areaMode": "2",

        "processMode": "0",
    }

    response = ctx.session.post(
        AREA_URL,
        data=payload
    )

    print_response_info(
        response
    )

    response.raise_for_status()

    save_response(
        response,
        f"07_area_{ctx.target_city.lower()}.html"
    )


# ============================================================
# STEP 8
# ============================================================

def step8_building(ctx):

    print()
    print("=" * 60)
    print(
        f"STEP 8: 館 - {ctx.city_name}"
    )
    print("=" * 60)

    payload = {
        "displayNo": "prwbb2000",
        "selectMenu": "1",

        "selectAreaCd": ctx.area_cd,
        "selectBldCd": BUILDING_CD,

        "selectPpsdCd": PURPOSE_CATEGORY_CD,
        "selectPpsCd": PURPOSE_CD,
        "selectPpsPpsdCd": PURPOSE_PURPOSE_CD,

        "selectInstNo": "0",

        "dispWeekNum": "0",
        "dispWeek": make_disp_week(),

        "submmitMode": "1",
        "transVacantMode": "7",
        "conditionMode": "2",

        "dispSelectInstBldCd": "",
        "dispSelectInstCd": "",

        "selectCommunityManageCd": ctx.community_cd,
        "selectCommunityPlaceCd": "0",

        "productMode": "3",
        "areaMode": "2",

        "processMode": "0",
    }

    response = ctx.session.post(
        BUILDING_URL,
        data=payload
    )

    print_response_info(
        response
    )

    response.raise_for_status()

    save_response(
        response,
        "08_building.html"
    )


# ============================================================
# STEP 9
# ============================================================

def step9_facility(ctx):

    print()
    print("=" * 60)
    print(
        f"STEP 9: 施設 - {ctx.city_name}"
    )
    print("=" * 60)

    payload = {
        "displayNo": "prwbb3000",
        "selectMenu": "1",

        "selectAreaCd": ctx.area_cd,
        "selectBldCd": BUILDING_CD,

        "selectPpsdCd": PURPOSE_CATEGORY_CD,
        "selectPpsCd": PURPOSE_CD,
        "selectPpsPpsdCd": PURPOSE_PURPOSE_CD,

        "selectInstNo": "0",

        "dispWeekNum": "0",
        "dispWeek": make_disp_week(),

        "submmitMode": "1",
        "transVacantMode": "7",
        "conditionMode": "2",

        "dispSelectInstBldCd": "",
        "dispSelectInstCd": "",

        "selectCommunityManageCd": ctx.community_cd,
        "selectCommunityPlaceCd": "0",

        "productMode": "3",
        "areaMode": "2",

        "processMode": "0",
    }

    response = ctx.session.post(
        FACILITY_URL,
        data=payload
    )

    print_response_info(
        response
    )

    response.raise_for_status()

    save_response(
        response,
        "09_facility.html"
    )

    return response


# ============================================================
# STEP 10
# ============================================================

def step10_search(ctx):

    print()
    print("=" * 60)
    print("STEP 10: 利用日・曜日検索条件")
    print("=" * 60)

    print(
        f"指定日: "
        f"{ctx.select_yy}-{ctx.select_mm}-{ctx.select_dd}"
    )

    selected_week = ctx.selected_week

    print(
        f"曜日設定: {selected_week}"
    )

    disp_week_num = sum(
        selected_week
    )


    select_yy = ctx.select_yy
    select_mm = ctx.select_mm
    select_dd = ctx.select_dd

    disp_yy = select_yy
    disp_mm = select_mm
    disp_dd = select_dd


    step10_data = [
        (
            "selectYY",
            select_yy
        ),
        (
            "selectMM",
            select_mm
        ),
        (
            "selectDD",
            select_dd
        ),
        (
            "displayNo",
            "prwbb4000"
        ),
        (
            "dispWeekNum",
            str(disp_week_num)
        ),
    ]


    for value in selected_week:

        step10_data.append(
            (
                "dispWeek",
                str(value)
            )
        )


    step10_data.extend([
        (
            "dispYY",
            disp_yy
        ),
        (
            "dispMM",
            disp_mm
        ),
        (
            "dispDD",
            disp_dd
        ),
        (
            "transVacantMode",
            "7"
        ),
        (
            "conditionMode",
            "2"
        ),
        (
            "submmitMode",
            "1"
        ),
        (
            "processMode",
            "0"
        ),
    ])


    response = ctx.session.post(
        VACANT_URL,
        data=step10_data
    )

    print_response_info(
        response
    )

    response.raise_for_status()

    response.encoding = "cp932"

    save_response(
        response,
        "11_vacant_result.html"
    )


    if "prwca1000.jsp" in response.text:

        print(
            "画面: prwca1000.jsp"
        )

    else:

        print(
            "警告: prwca1000.jsp "
            "を確認できません。"
        )


    if "空き状況の検索結果" in response.text:

        print(
            "空き状況検索結果画面を確認しました。"
        )

    else:

        print(
            "警告: 空き状況検索結果画面ではない可能性があります。"
        )


    return response


# ============================================================
# 施設1件解析
# ============================================================

def parse_facility_response(
    response,
    facility_index,
    filename,
    fallback_year=None
):

    response.encoding = "cp932"

    path = save_response(
        response,
        filename
    )

    result = parse_vacant_result(
        response.text,
        fallback_year=fallback_year
    )

    available_slots = (
        get_available_slots(
            result
        )
    )

    facility_name = (
        result.get("facility")
        or f"施設 {facility_index}"
    )


    print()
    print(
        f"[施設 {facility_index}] "
        f"{facility_name}"
    )


    if available_slots:

        for item in available_slots:

            print(
                f"  {item.get('date')} "
                f"{item.get('time')}"
            )

    else:

        print(
            "  空きなし"
        )


    return {
        "index": facility_index,
        "result": result,
        "available_slots": available_slots,
        "html": path,
    }


# ============================================================
# 次施設POSTデータ作成
# ============================================================

def make_next_facility_data(
    soup,
    facility_index
):
    """
    JavaScript:

        doInstSrchVacantAction(
            obj,
            action,
            transVacantMode,
            srchSelectInstNo,
            gSrchSelectInstMax
        )

    の動作を再現する。

    JavaScriptではform全体をsubmitしているため、
    hidden値を数個だけ作るのではなく、
    form全体を取得する。

    その後、

        transVacantMode = 6
        srchSelectInstNo = 次施設番号

    の2項目だけを書き換える。
    """

    # --------------------------------------------------------
    # form全体を取得
    # --------------------------------------------------------

    data = extract_form_data(
        soup
    )


    # --------------------------------------------------------
    # JavaScriptと同じ
    #
    # transVacantMode = 6
    # --------------------------------------------------------

    data = set_post_value(
        data,
        "transVacantMode",
        "6"
    )


    # --------------------------------------------------------
    # JavaScriptと同じ
    #
    # obj.srchSelectInstNo.value =
    #     srchSelectInstNo + 1
    #
    # 呼び出し側ではすでに次番号を渡す。
    # --------------------------------------------------------

    data = set_post_value(
        data,
        "srchSelectInstNo",
        str(facility_index)
    )


    return data


# ============================================================
# 次施設レスポンス判定
# ============================================================

def check_next_facility_response(
    response
):
    """
    次施設POSTのレスポンスが
    本当に空き状況画面なのか確認する。
    """

    text = response.text

    soup = BeautifulSoup(
        text,
        "html.parser"
    )


    # --------------------------------------------------------
    # 空き状況テーブル
    # --------------------------------------------------------

    table = soup.select_one(
        "table.rsvakitable"
    )

    if table is not None:

        return (
            True,
            "table.rsvakitable を確認"
        )


    # --------------------------------------------------------
    # エラー・タイムアウト系
    # --------------------------------------------------------

    error_keywords = [
        "セッション",
        "タイムアウト",
        "エラー",
        "Error",
        "exception",
        "System Error",
    ]


    found_errors = []

    for keyword in error_keywords:

        if keyword in text:

            found_errors.append(
                keyword
            )


    if found_errors:

        return (
            False,
            "エラー／タイムアウトの可能性: "
            + ", ".join(found_errors)
        )


    # --------------------------------------------------------
    # ログイン画面等
    # --------------------------------------------------------

    if (
        "ログイン" in text
        or
        "login" in text.lower()
    ):

        return (
            False,
            "ログイン画面の可能性"
        )


    # --------------------------------------------------------
    # その他
    # --------------------------------------------------------

    return (
        False,
        "空き状況テーブルなし"
    )


# ============================================================
# STEP 11以降
# 施設を最後まで巡回
# ============================================================

def scan_all_facilities(
    ctx,
    first_response
):

    facilities = []


    # ========================================================
    # 施設0
    # ========================================================

    first_facility = parse_facility_response(
        first_response,
        FIRST_FACILITY_INDEX,
        "11_facility_0.html",
        fallback_year=ctx.select_yy
    )

    facilities.append(
        first_facility
    )


    # ========================================================
    # 次施設
    # ========================================================

    next_index = (
        FIRST_FACILITY_INDEX + 1
    )


    while True:

        print()
        print("=" * 60)
        print(
            f"次施設取得: "
            f"srchSelectInstNo={next_index}"
        )
        print("=" * 60)


        # ----------------------------------------------------
        # 前回施設のHTML
        # ----------------------------------------------------

        previous_html = (
            facilities[-1]["html"]
        )


        previous_soup = BeautifulSoup(
            previous_html.read_text(
                encoding="utf-8"
            ),
            "html.parser"
        )


        # ----------------------------------------------------
        # 次施設POST
        # ----------------------------------------------------

        try:

            step_data = make_next_facility_data(
                previous_soup,
                next_index
            )

        except Exception as e:

            print()
            print(
                "次施設POSTデータ作成失敗:"
            )

            print(e)

            break


        # ----------------------------------------------------
        # POST内容確認
        # ----------------------------------------------------

        print_post_data(
            step_data
        )


        # ----------------------------------------------------
        # 特に重要な項目を確認
        # ----------------------------------------------------

        print()
        print("次施設用重要パラメータ:")

        important_names = [
            "displayNo",
            "wselectInstCd",
            "wselectUseYMD",
            "wselectStZoneNo",
            "dispStime",
            "dispStZoneNo",
            "dispEtime",
            "dispEtZoneNo",
            "transVacantMode",
            "srchSelectInstNo",
            "selectStime",
            "selectStZoneNo",
            "selectEtime",
            "selectEtZoneNo",
            "selectSize",
            "processMode",
        ]


        for important_name in important_names:

            values = [
                value
                for name, value in step_data
                if name == important_name
            ]

            if values:
                """
                print(
                    f"  {important_name} = "
                    f"{values}"
                )
                """


        # ----------------------------------------------------
        # POST
        # ----------------------------------------------------

        try:

            response = ctx.session.post(
                VACANT_URL,
                data=step_data,
                timeout=60
            )

        except requests.Timeout:

            print()
            print(
                "次施設POSTがタイムアウトしました。"
            )

            print(
                "次施設なしとは判定せず、"
                "ここで巡回を終了します。"
            )

            break


        print_response_info(
            response
        )


        response.raise_for_status()

        response.encoding = "cp932"


        # ----------------------------------------------------
        # HTML保存
        # ----------------------------------------------------

        filename = (
            f"{next_index + 11:02d}"
            f"_facility_{next_index}.html"
        )


        path = save_response(
            response,
            filename
        )


        # ----------------------------------------------------
        # レスポンス判定
        # ----------------------------------------------------

        valid, reason = (
            check_next_facility_response(
                response
            )
        )


        print()
        print(
            f"次施設レスポンス判定: "
            f"{reason}"
        )


        # ----------------------------------------------------
        # 空き状況画面ではない
        # ----------------------------------------------------

        if not valid:

            print()
            print(
                "次施設が存在しないとは断定しません。"
            )

            print(
                "今回のレスポンスでは"
                "次施設結果を取得できませんでした。"
            )

            break


        # ----------------------------------------------------
        # 施設解析
        # ----------------------------------------------------

        result = parse_vacant_result(
            response.text,
            fallback_year=ctx.select_yy
        )


        available_slots = (
            get_available_slots(
                result
            )
        )


        facility_info = {
            "index": next_index,
            "result": result,
            "available_slots": available_slots,
            "html": path,
        }


        facilities.append(
            facility_info
        )


        # ----------------------------------------------------
        # 現在施設表示
        # ----------------------------------------------------

        facility_name = (
            result.get("facility")
            or f"施設 {next_index}"
        )


        print()
        print(
            f"[施設 {next_index}] "
            f"{facility_name}"
        )


        if available_slots:

            for item in available_slots:

                print(
                    f"  {item.get('date')} "
                    f"{item.get('time')}"
                )

        else:

            print(
                "  空きなし"
            )


        # ----------------------------------------------------
        # 次施設番号
        # ----------------------------------------------------

        next_index += 1


    return facilities


# ============================================================
# Main
# ============================================================
def main(
    city_key=None,
    search_date=None,
    selected_week=None
):

    # ========================================================
    # 自治体設定
    # ========================================================

    if city_key is None:
        city_key = TARGET_CITY

    if city_key not in CITY_SETTINGS:
        raise ValueError(
            f"不正なcity_key: {city_key}"
        )

    city = CITY_SETTINGS[city_key]

    city_name = city["name"]
    community_cd = city["community_cd"]
    area_cd = city["area_cd"]

    # ========================================================
    # 検索日
    # ========================================================

    select_yy = DEFAULT_SELECT_YY
    select_mm = DEFAULT_SELECT_MM
    select_dd = DEFAULT_SELECT_DD

    if search_date is not None:
        select_yy = str(search_date.year)
        select_mm = str(search_date.month)
        select_dd = str(search_date.day)

    # ========================================================
    # 曜日設定
    # ========================================================

    if selected_week is None:
        selected_week = DEFAULT_SELECTED_WEEK.copy()
    else:
        if len(selected_week) != 8:
            raise ValueError(
                "selected_week は8個の値が必要です"
            )
        selected_week = list(selected_week)

    print()
    print("=" * 70)
    print("愛知県施設予約 空き状況検索")
    print("=" * 70)

    print(
        f"自治体: {city_name}"
    )

    print(
        f"COMMUNITY_CD: {community_cd}"
    )

    print(
        f"AREA_CD: {area_cd}"
    )

    print(
        f"利用目的: バレーボール"
    )

    print(
        f"検索日: "
        f"{select_yy}-{select_mm}-{select_dd}"
    )

    print("=" * 70)

    # ========================================================
    # Session
    # ========================================================

    session = requests.Session()

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/151.0.0.0 Safari/537.36"
        )
    })

    ctx = SearchContext(
        session=session,
        target_city=city_key,
        city_name=city_name,
        community_cd=community_cd,
        area_cd=area_cd,
        select_yy=select_yy,
        select_mm=select_mm,
        select_dd=select_dd,
        selected_week=selected_week,
    )

    # ========================================================
    # STEP 1
    # ========================================================

    step1_top(ctx)

    # ========================================================
    # STEP 2
    # ========================================================

    step2_reserve_menu(ctx)

    # ========================================================
    # STEP 3
    # ========================================================

    step3_purpose_category(ctx)

    # ========================================================
    # STEP 4
    # ========================================================

    step4_sports_category(ctx)

    # ========================================================
    # STEP 5
    # ========================================================

    step5_volleyball(ctx)

    # ========================================================
    # STEP 6
    # ========================================================

    step6_community(ctx)

    # ========================================================
    # STEP 7
    # ========================================================

    step7_area(ctx)

    # ========================================================
    # STEP 8
    # ========================================================

    step8_building(ctx)

    # ========================================================
    # STEP 9
    # ========================================================

    step9_facility(ctx)

    # ========================================================
    # STEP 10
    # ========================================================

    first_response = step10_search(ctx)

    # ========================================================
    # STEP 11以降
    # ========================================================

    print()
    print("=" * 60)
    print("施設巡回開始")
    print("=" * 60)

    facilities = scan_all_facilities(
        ctx,
        first_response
    )

    # ========================================================
    # 最終結果
    # ========================================================

    print_available_summary(
        ctx,
        facilities
    )

    # ========================================================
    # 完了
    # ========================================================

    print()
    print("=" * 60)
    print("巡回完了")
    print("=" * 60)

    print(
        f"取得施設数: {len(facilities)}"
    )

    return facilities

# ============================================================
# エントリーポイント
# ============================================================

if __name__ == "__main__":

    main()
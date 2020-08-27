# pylint: skip-file
import datetime
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

from dms_daemon import CONFIG


def notice_list():
    for root, _, files in os.walk("/data/marble/nemweb/MARKET_NOTICES/"):
        for f in files:
            yield os.path.join(root, f)


def read_notice(fn="/data/marble/nemweb/MARKET_NOTICES/2017-12-21/60425.txt"):
    with open(fn, "r") as f:
        return f.readlines()


def check_notice_list():
    for _, _, files in os.walk("/data/marble/nemweb/MARKET_NOTICES/"):
        for f in files:
            None
            # check_notice(fn=os.path.join(root,f))
            # warning, uncommenting could send lots of slack alerts


def check_notice(
    fn,
    notice_types=[
        "POWER SYSTEM EVENTS",
        "GENERAL NOTICE",
        "RESERVE NOTICE",
        "MARKET INTERVENTION",
    ],
):
    market_notice = read_notice(fn)

    if any([nt in market_notice[11] for nt in notice_types]):
        slack_alert(market_notice)

    if market_notice[14].find("Forecast Lack Of Reserve Level 2") != -1:
        send(market_notice)

    if market_notice[12].find("LRC/LOR1/LOR2/LOR3") != -1:
        try:
            reserve_notice(market_notice)
        except Exception as E:
            r = requests.post(
                "https://hooks.slack.com/services/{0}".format(
                    CONFIG["slack_hooks"]["error_message"]
                ),
                json={"text": E.args[0]},
            )
            raise E


def slack_alert(market_notice):
    mn_text = "".join(market_notice)
    message_type = market_notice[11].split(":")[1].strip()
    message = "*Market Notice: {0}*\n\n{1}".format(message_type, mn_text)

    requests.post(
        "https://hooks.slack.com/services/{0}".format(
            CONFIG["slack_hooks"]["market_notice"]
        ),
        json={"text": message},
    )


def reserve_notice(market_notice):
    lor_pattern = re.compile("LOR([0-9]{1})")
    lor_match = re.search(lor_pattern, market_notice[14])
    if lor_match == None:
        if "RESERVE NOTICE" in market_notice[14]:
            None
        else:
            raise Exception("No LOR in external reference")
    else:
        lor_notice(market_notice, lor_match)


def lor_notice(market_notice, lor_match):
    region_pattern = re.compile(r"the (.{2,15}) \w{1}egion")
    region_match = re.search(region_pattern, market_notice[14])
    if region_match == None:
        raise Exception("No region in external reference")

    lor_category_pattern = re.compile(
        r"(\w{1}orecast|\w{1}ctual|\w{1}ancellation)"
    )
    lor_category_match = re.search(lor_category_pattern, market_notice[14])
    if lor_category_match == None:
        raise Exception("No LOR type (not Forecast or Actual)")
    elif lor_category_match.group(1).lower() == "cancellation":
        lor_cancellation_template(
            int(lor_match.group(1)),
            region_match.group(1),
            lor_category_match.group(1),
        )
    else:
        lor_update(market_notice, lor_match, region_match, lor_category_match)
    return region_match, lor_category_match


def lor_update(market_notice, lor_match, region_match, lor_category_match):

    if market_notice[14].find("Update") != -1:
        lor_type = "New"
    else:
        lor_type = "Update"

    from_time2 = None
    to_time2 = None

    try:
        from_time = time_parse(string="".join(market_notice), start="(F|f)rom")
        to_time = time_parse(string="".join(market_notice), start="(T|t)o")
    except:
        try:
            from_time, to_time = time_parse2(string="".join(market_notice))
        except:
            try:
                from_time, to_time = time_parse3(string="".join(market_notice))
            except:
                try:
                    (
                        from_time,
                        to_time,
                        from_time2,
                        to_time2,
                    ) = multi_time_parse(string="".join(market_notice))
                except:
                    raise Exception("Bad datestring format")

    required = reserve_required(market_notice)
    available = reserve_available(market_notice)

    lor_template(
        int(lor_match.group(1)),
        lor_category_match.group(1),
        region_match.group(1),
        lor_type,
        from_time,
        to_time,
        int(required),
        int(available),
        from_dt2=from_time2,
        to_dt2=to_time2,
    )


def reserve_available(market_notice):
    reserve_available_pattern = re.compile(
        r"reserve available is (\d{3,4}) MW"
    )
    reserve_available_match = re.search(
        reserve_available_pattern, "".join(market_notice)
    )
    if reserve_available_match == None:
        raise Exception("Bad reserve requirement format")
    return reserve_available_match.group(1)


def reserve_required(market_notice):
    reserve_requirement_pattern = re.compile(
        r"reserve requirement is (\d{3,4}|\d{1},\d{3}) MW"
    )
    reserve_requirement_match = re.search(
        reserve_requirement_pattern, "".join(market_notice)
    )
    if reserve_requirement_match == None:
        raise Exception("Bad reserve requirement format")
    return reserve_requirement_match.group(1).replace(",", "")


def lor_template(
    level,
    category,
    region,
    lor_type,
    from_dt,
    to_dt,
    reserve_req,
    reserve_avail,
    from_dt2=None,
    to_dt2=None,
):
    colors = {1: "#ffc100", 2: "#ff7400", 3: "ff0000"}
    title = "LOR{0} {2} for {1} ({3})".format(
        level, region, category.lower(), lor_type.lower()
    )
    details = "({0}MW shortfall between {1} and {2})".format(
        reserve_req - reserve_avail, from_dt, to_dt
    )
    if from_dt2 != None:
        details = "({0}MW shortfall between {1} to {2}, and {3} to {4})".format(
            reserve_req - reserve_avail, from_dt, to_dt, from_dt2, to_dt2
        )
    r = requests.post(
        "https://hooks.slack.com/services/{0}".format(
            CONFIG["slack_hooks"]["reserve_notice"]
        ),
        json={
            "attachments": [
                {"title": title, "color": colors[level]},
                {"text": details},
            ]
        },
    )


def lor_cancellation_template(level, region, category):
    colors = {1: "#36a64f", 2: "#ffc100", 3: "#ff7400"}
    title = "LOR{0} {2} for {1}".format(level, region, category.lower())
    requests.post(
        "https://hooks.slack.com/services/{0}".format(
            CONFIG["slack_hooks"]["reserve_notice"]
        ),
        json={"attachments": [{"title": title, "color": colors[level]}]},
    )


def time_parse(string, start="(F|f)rom"):
    time_pattern = re.compile(
        r"{0} (\d{{2}})(\d{{2}}) hrs (\d{{2}})/(\d{{2}})/(\d{{4}})".format(
            start
        )
    )
    time_match = re.search(time_pattern, string)
    _, H, M, d, m, y = time_match.groups()
    return datetime.datetime(int(y), int(m), int(d), int(H), int(M))


def time_parse2(string):
    time_pattern = re.compile(
        r"(F|f)rom (\d{2})(\d{2}) hrs (T|t)o (\d{2})(\d{2}) hrs (\d{2})/(\d{2})/(\d{4})"
    )
    time_match = re.search(time_pattern, string)
    _, H1, M1, _, H2, M2, d, m, y = time_match.groups()
    return (
        datetime.datetime(int(y), int(m), int(d), int(H1), int(M1)),
        datetime.datetime(int(y), int(m), int(d), int(H2), int(M2)),
    )


def time_parse3(string):
    time_pattern = re.compile(
        r"(F|f)rom (\d{2})(\d{2}) hrs (T|t)o (\d{2})(\d{2}) hrs on (\d{2})/(\d{2})/(\d{4})"
    )
    time_match = re.search(time_pattern, string)
    _, H1, M1, _, H2, M2, d, m, y = time_match.groups()
    return (
        datetime.datetime(int(y), int(m), int(d), int(H1), int(M1)),
        datetime.datetime(int(y), int(m), int(d), int(H2), int(M2)),
    )


def multi_time_parse(string):
    time_pattern = re.compile(
        r"(F|f)rom (\d{2})(\d{2}) hrs (T|t)o (\d{2})(\d{2}) hrs and (\d{2})(\d{2}) hrs (T|t)o (\d{2})(\d{2}) hrs (\d{2})/(\d{2})/(\d{4})"
    )
    time_match = re.search(time_pattern, string)
    _, H1, M1, _, H2, M2, H3, M3, _, H4, M4, d, m, y = time_match.groups()
    return (
        datetime.datetime(int(y), int(m), int(d), int(H1), int(M1)),
        datetime.datetime(int(y), int(m), int(d), int(H2), int(M2)),
        datetime.datetime(int(y), int(m), int(d), int(H3), int(M3)),
        datetime.datetime(int(y), int(m), int(d), int(H4), int(M4)),
    )


def login():
    server = smtplib.SMTP("smtp.gmail.com:587")
    server.ehlo()
    server.starttls()
    server.login(CONFIG["gmail"]["username"], CONFIG["gmail"]["password"])
    return server


def create_msg(market_notice):
    mn_text = "".join(market_notice)
    message_type = market_notice[11].split(":")[1].strip()

    msg = MIMEMultipart()
    msg["From"] = CONFIG["gmail"]["username"]
    msg["To"] = CONFIG["gmail"]["send_to"]
    msg["Subject"] = message_type
    msg.add_header("Content-Type", "text")

    msg.attach(MIMEText(mn_text, "plain"))
    return msg


def send(market_notice):
    server = login()
    msg = create_msg(market_notice)
    server.sendmail(
        CONFIG["gmail"]["username"],
        CONFIG["gmail"]["send_to"],
        msg.as_string(),
    )
    server.close()


test_file = "/data/marble/nemweb/MARKET_NOTICES/2017-10-24/59591.txt"

line_12 = [
    "Details of Non-conformance/Conformance",
    "Emergency events/conditions",
    "Inter-Regional Transfer limit variation",
    "LRC/LOR1/LOR2/LOR3",
    "New/Modified Constraints",
    "Prices are not firm due to an MII or OCD event",
    "Prices have been reviewed and remain unchanged",
    "Reclassify contingency events",
    "Reserve Contract / Direction / Instruction",
    "Status of Market Systems",
    "Subjects not covered in specific notices",
]

line_11 = [
    "CONSTRAINTS",
    "GENERAL NOTICE",
    "INTER-REGIONAL TRANSFER",
    "MARKET INTERVENTION",
    "MARKET SYSTEMS",
    "NON-CONFORMANCE",
    "POWER SYSTEM EVENTS",
    "PRICES SUBJECT TO REVIEW",
    "PRICES UNCHANGED",
    "RECLASSIFY CONTINGENCY",
    "RESERVE NOTICE",
]

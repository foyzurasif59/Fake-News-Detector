from urllib.request import Request, urlopen
from urllib.parse import quote, urlparse
from html.parser import HTMLParser
import re



# HTML READER


class Reader(HTMLParser):

    def __init__(self):
        super().__init__()
        self.title = ""
        self.text = ""
        self.intitle = False
        self.skip = False

    def handle_starttag(self, tag, attrs):

        if tag == "title":
            self.intitle = True

        if tag in ["script", "style", "noscript"]:
            self.skip = True

    def handle_endtag(self, tag):

        if tag == "title":
            self.intitle = False

        if tag in ["script", "style", "noscript"]:
            self.skip = False

    def handle_data(self, data):

        if self.skip:
            return

        data = re.sub(r"\s+", " ", data).strip()

        if self.intitle:
            self.title += data + " "

        if len(data) > 20:
            self.text += data + " "



# GET WEB PAGE


def get(url):

    try:

        req = Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        return urlopen(req, timeout=10).read().decode(
            "utf-8", "ignore"
        )

    except Exception as e:

        print("Web error:", e)

        return ""



# READ ARTICLE


def article(url):

    html = get(url)

    if not html:
        return "", ""

    p = Reader()
    p.feed(html)

    return p.title.strip(), p.text.strip()



# GOOGLE NEWS


def news(title):

    try:

        url = (
            "https://news.google.com/rss/search?q="
            + quote(title)
            + "&hl=en-US&gl=US&ceid=US:en"
        )

        xml = get(url)

        titles = re.findall(
            r"<title>(.*?)</title>",
            xml,
            re.S
        )

        return [
            re.sub("<.*?>", "", x).strip()
            for x in titles[1:9]
        ]

    except:

        return []



# WORDS


def words(text):

    return set(
        re.findall(
            r"[a-zA-Z]{3,}",
            text.lower()
        )
    )



# SIMILARITY


def similarity(a, b):

    a = words(a)
    b = words(b)

    if not a or not b:
        return 0

    return round(
        len(a & b) / len(a | b) * 100,
        1
    )


# CLICKBAIT


def clickbait(title):

    bad = [
        "shocking",
        "breaking",
        "unbelievable",
        "secret",
        "exposed",
        "you won't believe",
        "must see",
        "urgent",
        "miracle",
        "viral",
        "incredible"
    ]

    score = sum(
        x in title.lower()
        for x in bad
    ) * 10

    score += title.count("!") * 5
    score += title.count("?") * 3

    return min(score, 100)


# SUSPICIOUS WORDS


def suspicious(text):

    bad = [
        "shocking",
        "secret",
        "exposed",
        "miracle",
        "conspiracy",
        "guaranteed",
        "fake",
        "hoax",
        "unbelievable",
        "insane",
        "urgent",
        "viral"
    ]

    n = sum(
        x in text.lower()
        for x in bad
    )

    return min(n * 8, 100)



# SOURCE CHECK


def source_score(url):

    site = urlparse(url).netloc.lower()

    trusted = [
        "reuters.com",
        "apnews.com",
        "bbc.com",
        "bbc.co.uk",
        "npr.org",
        "cnn.com",
        "nytimes.com",
        "washingtonpost.com",
        "theguardian.com",
        "aljazeera.com",
        "cbsnews.com",
        "nbcnews.com"
    ]

    return 25 if any(x in site for x in trusted) else 0



# ANALYSIS


def analyze(url, title, text):

    score = 50

    if url:

        if url.lower().startswith("https://"):
            score += 5

        score += source_score(url)

    cb = clickbait(title)

    sp = suspicious(
        title + " " + text[:3000]
    )

    score -= cb // 4
    score -= sp // 5

    results = news(title)

    matches = [
        similarity(title, x)
        for x in results
    ]

    best = max(matches, default=0)

    if best >= 50:
        score += 15

    elif best >= 30:
        score += 8

    elif best < 15:
        score -= 8

    score = max(
        0,
        min(100, score)
    )

    return score, cb, sp, best, results



# RUN PROGRAM


print("=" * 60)
print("        LIVE NEWS CREDIBILITY ANALYZER")
print("=" * 60)

url = input(
    "\nEnter News URL (leave empty for headline): "
).strip()

headline = ""

if url:

    print("\nReading live article...")

    headline, text = article(url)

    if not headline:

        print("\nCould not read this webpage.")
        print("Try entering the headline manually.")

        headline = input(
            "\nEnter headline: "
        ).strip()

        text = ""

else:

    headline = input(
        "\nEnter News Headline: "
    ).strip()

    text = ""


if headline:

    print("\nChecking live news sources...")

    score, cb, sp, best, results = analyze(
        url,
        headline,
        text
    )

    print("\n" + "=" * 60)
    print("                 RESULT")
    print("=" * 60)

    print("\nHeadline:")
    print(headline)

    print("\nCredibility Score:", score, "/100")

    if score >= 75:

        print("Verdict: 🟢 LIKELY CREDIBLE")

    elif score >= 50:

        print("Verdict: 🟡 NEEDS VERIFICATION")

    else:

        print("Verdict: 🔴 HIGH RISK / SUSPICIOUS")

    print("\nClickbait Score:", cb, "/100")
    print("Suspicious Language:", sp, "/100")
    print("Best News Match:", best, "%")
    print("Other Reports Found:", len(results))

    print("\n" + "-" * 60)
    print("CORROBORATING NEWS")
    print("-" * 60)

    if results:

        for i, x in enumerate(results, 1):

            print(
                f"{i}. {x}"
            )

            print(
                f"   Similarity: {similarity(headline, x)}%"
            )

    else:

        print("No matching reports found.")

    print("\n" + "=" * 60)
    print("NOTE: This is a credibility indicator,")
    print("not proof that a news story is true or false.")
    print("=" * 60)

else:

    print("\nNo headline provided.")

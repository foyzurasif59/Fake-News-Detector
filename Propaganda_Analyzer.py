import tkinter as tk
from tkinter import ttk, messagebox
from urllib.request import Request, urlopen
from urllib.parse import quote, urlparse
from html.parser import HTMLParser
import re


# ---------- WEB PAGE READER ----------

class Reader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.text = ""
        self.inside_title = False
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.inside_title = True
        if tag in ["script", "style", "noscript"]:
            self.skip = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.inside_title = False
        if tag in ["script", "style", "noscript"]:
            self.skip = False

    def handle_data(self, data):
        if self.skip:
            return

        data = re.sub(r"\s+", " ", data).strip()

        if self.inside_title:
            self.title += data + " "

        if len(data) > 20:
            self.text += data + " "


# ---------- DOWNLOAD PAGE ----------

def get_page(url):
    try:
        req = Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        page = urlopen(req, timeout=10)
        return page.read().decode("utf-8", "ignore")

    except:
        return ""


# ---------- READ ARTICLE ----------

def read_article(url):
    html = get_page(url)

    if not html:
        return "", ""

    p = Reader()
    p.feed(html)

    title = p.title.strip()
    text = p.text.strip()

    return title, text


# ---------- GOOGLE NEWS SEARCH ----------

def search_news(title):
    try:
        url = (
            "https://news.google.com/rss/search?q="
            + quote(title)
            + "&hl=en-US&gl=US&ceid=US:en"
        )

        xml = get_page(url)

        titles = re.findall(
            r"<title>(.*?)</title>",
            xml,
            re.S
        )

        titles = [
            re.sub("<.*?>", "", x).strip()
            for x in titles[1:]
        ]

        return titles[:8]

    except:
        return []


# ---------- SIMPLE TEXT TO WORDS ----------

def words(text):
    return set(
        re.findall(
            r"[a-zA-Z]{3,}",
            text.lower()
        )
    )


# ---------- TITLE SIMILARITY ----------

def similarity(a, b):

    a = words(a)
    b = words(b)

    if not a or not b:
        return 0

    return round(
        len(a & b) / len(a | b) * 100
    )


# ---------- CLICKBAIT ----------

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
        "they don't want you to know",
        "incredible"
    ]

    score = sum(
        x in title.lower()
        for x in bad
    ) * 10

    score += title.count("!") * 5
    score += title.count("?") * 3

    return min(score, 100)


# ---------- SUSPICIOUS WORDS ----------

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


# ---------- SOURCE CHECK ----------

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
        "nbcnews.com",
        "abcnews.go.com"
    ]

    for x in trusted:

        if x in site:
            return 25

    return 0


# ---------- MAIN ANALYSIS ----------

def analyze(url, headline):

    score = 50

    if url:

        if url.lower().startswith("https://"):
            score += 5

        score += source_score(url)

    cb = clickbait(headline)
    sp = suspicious(headline)

    score -= cb // 4
    score -= sp // 5

    results = search_news(headline)

    matches = [
        similarity(headline, x)
        for x in results
    ]

    best = max(matches, default=0)

    if best >= 50:
        score += 15

    elif best >= 30:
        score += 8

    elif best < 15:
        score -= 8

    score = max(0, min(100, score))

    return score, cb, sp, best, results


# ---------- GUI ----------

root = tk.Tk()

root.title("Live News Credibility Analyzer")
root.geometry("1000x700")
root.configure(bg="#101827")


# ---------- STYLE ----------

style = ttk.Style()
style.theme_use("clam")

style.configure(
    "TButton",
    font=("Segoe UI", 11, "bold"),
    padding=10
)

style.configure(
    "TEntry",
    font=("Segoe UI", 12)
)

style.configure(
    "TLabel",
    background="#101827",
    foreground="white"
)


# ---------- TITLE ----------

tk.Label(
    root,
    text="LIVE NEWS CREDIBILITY ANALYZER",
    font=("Segoe UI", 24, "bold"),
    bg="#101827",
    fg="white"
).pack(pady=(25, 5))


tk.Label(
    root,
    text="Check a live news article using simple credibility signals",
    font=("Segoe UI", 11),
    bg="#101827",
    fg="#9ca3af"
).pack()


# ---------- INPUT ----------

box = tk.Frame(
    root,
    bg="#172235"
)

box.pack(
    fill="x",
    padx=30,
    pady=25
)


tk.Label(
    box,
    text="News URL",
    font=("Segoe UI", 11, "bold"),
    bg="#172235",
    fg="white"
).pack(
    anchor="w",
    padx=20,
    pady=(15, 5)
)


url_entry = ttk.Entry(box)

url_entry.pack(
    fill="x",
    padx=20,
    ipady=8
)


tk.Label(
    box,
    text="OR enter a news headline",
    font=("Segoe UI", 10),
    bg="#172235",
    fg="#9ca3af"
).pack(
    anchor="w",
    padx=20,
    pady=(12, 5)
)


headline_entry = ttk.Entry(box)

headline_entry.pack(
    fill="x",
    padx=20,
    ipady=8
)


# ---------- RESULT ----------

result = tk.Frame(
    root,
    bg="#172235"
)

result.pack(
    fill="both",
    expand=True,
    padx=30
)


score_label = tk.Label(
    result,
    text="--",
    font=("Segoe UI", 42, "bold"),
    bg="#172235",
    fg="white"
)

score_label.pack(pady=(20, 0))


status_label = tk.Label(
    result,
    text="Enter a URL or headline",
    font=("Segoe UI", 18, "bold"),
    bg="#172235",
    fg="#9ca3af"
)

status_label.pack(pady=5)


details = tk.Label(
    result,
    text="",
    justify="left",
    font=("Segoe UI", 11),
    bg="#172235",
    fg="#d1d5db"
)

details.pack(pady=10)


# ---------- SEARCH RESULTS ----------

news_box = tk.Text(
    result,
    height=8,
    bg="#0f172a",
    fg="#dbeafe",
    insertbackground="white",
    font=("Segoe UI", 10),
    relief="flat"
)

news_box.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=15
)


# ---------- ANALYZE ----------

def check():

    url = url_entry.get().strip()
    headline = headline_entry.get().strip()

    if not url and not headline:

        messagebox.showwarning(
            "Missing information",
            "Enter a news URL or headline."
        )

        return


    if url:

        status_label.config(
            text="Reading live article..."
        )

        root.update()

        title, text = read_article(url)

        if title:

            headline = title

        if not headline:

            messagebox.showerror(
                "Error",
                "Could not extract the article headline."
            )

            return


    status_label.config(
        text="Checking live news sources..."
    )

    root.update()


    score, cb, sp, best, results = analyze(
        url,
        headline
    )


    # ---------- VERDICT ----------

    if score >= 75:

        verdict = "🟢 LIKELY CREDIBLE"
        color = "#22c55e"

    elif score >= 50:

        verdict = "🟡 NEEDS VERIFICATION"
        color = "#f59e0b"

    else:

        verdict = "🔴 HIGH RISK / SUSPICIOUS"
        color = "#ef4444"


    score_label.config(
        text=f"{score}/100",
        fg=color
    )

    status_label.config(
        text=verdict,
        fg=color
    )


    details.config(
        text=
        f"Headline:\n{headline[:180]}\n\n"
        f"Clickbait score:       {cb}/100\n"
        f"Suspicious language:   {sp}/100\n"
        f"Best news match:       {best:.1f}%\n"
        f"Other reports found:   {len(results)}\n\n"
        "This score is an indicator, not proof that a story is true or false."
    )


    news_box.delete(
        "1.0",
        tk.END
    )


    if results:

        news_box.insert(
            tk.END,
            "LIVE CORROBORATING NEWS\n"
            "========================\n\n"
        )

        for i, x in enumerate(results, 1):

            news_box.insert(
                tk.END,
                f"{i}. {x}\n\n"
            )

    else:

        news_box.insert(
            tk.END,
            "No matching news reports were found."
        )


# ---------- BUTTON ----------

ttk.Button(
    box,
    text="🔍  ANALYZE NEWS",
    command=check
).pack(
    pady=18
)


# ---------- START ----------

root.mainloop()

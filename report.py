import os
import re
import json
import datetime
import pytz
import collections
import itertools
import math
import subprocess
import sys
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from PIL import Image
from PyPDF2 import PdfFileReader, PdfFileWriter
from io import BytesIO
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, Paragraph
from wordcloud import WordCloud

class Visualization:
    def __init__(self, watch_history_file, search_history_file, comments_history_file, like_history_file, image_dir):
        self.watch_history_file = watch_history_file
        self.search_history_file = search_history_file
        self.comments_history_file = comments_history_file
        self.like_history_file = like_history_file
        self.image_dir = image_dir

    def debug_print(self, msg):
        print("[DEBUG] ", msg)

    def process_data(self):
        # Read watch history HTML file
        with open(self.watch_history_file, "r", encoding="utf-8") as f:
            self.html_watch = f.read()

        # Read search history HTML file
        with open(self.search_history_file, "r", encoding="utf-8") as f:
            self.html_search = f.read()

        # Read comments history HTML file
        try:
            with open(self.comments_history_file, "r", encoding="utf-8") as f:
                self.html_comment = f.read()
        except Exception as e:
            self.debug_print("Could not parse comments:", str(e))

        # Read like history JSON file
        with open(self.like_history_file, "rb") as f:
            self.like_data = json.load(f)

    def find_links(self):
        # Search for all links in the watch history HTML
        links = []
        for translation in (r"""Watched\xa0<a href=\"([^\"]*)\">[^<]*<\/a>""", r"""<a href=\"([^\"]*)\">[^<]*<\/a>\xa0angesehen"""):
            links += self.raw_find_links(translation)
        return links

    def raw_find_links(self, translation):
        pattern = re.compile(translation)
        match_list = pattern.findall(str(self.html_watch))
        return [match for match in match_list if type(match) == str]

    def find_times(self):
        times = []
        for translation in ((r"""<\/a><br><a href=\"[^\"]*\">[^<]*<\/a><br>(\D*) (\d\d?), (\d\d\d\d), (\d\d?):(\d\d?):(\d\d?) (AM|PM) ([^<]*)<\/div>""", "%s %s, %s, %s:%s:%s %s", "%b %d, %Y, %I:%M:%S %p"), (r"""\xa0angesehen<br><a href=\"[^\"]*\">[^<]*<\/a><br>(\d\d?)\.(\d\d?)\.(\d\d\d\d), (\d\d?):(\d\d?):(\d\d?) ([^<]*)<\/div>""", "%s.%s.%s %s:%s:%s", "%d.%m.%Y %H:%M:%S")):
            times += self.raw_find_times(*translation)
        return times

    def raw_find_times(self, regex, timegex, timegex2):
        pattern = re.compile(regex)
        match_list = pattern.findall(str(self.html_watch))
        for time in match_list:
            times.append(pytz.timezone(time[-1]).localize(datetime.datetime.strptime(timegex % (time[:-1]), timegex2)))
        return times

    def search_history(self):
        search_raw = []
        search_clean = []
        pattern = re.compile(r"search_query=[^%].*?>")
        match_list = pattern.findall(str(self.html_search))
        for match in match_list:
            match = match[13:][:-2]
            match = match.split("+")
            search_raw.append(match)
        for word in list(itertools.chain.from_iterable(search_raw)):
            if "%" not in word:
                search_clean.append(word)
        return search_raw, search_clean

    def comment_history(self):
        try:
            pattern = re.compile(r"""<a href=['"].*?['"]>""")
            match_list = pattern.findall(str(self.html_comment))
            link = match_list[-1][9:][:-2]
            return link, match_list
        except Exception as e:
            self.debug_print("Error parsing comments:", str(e))

    def like_history(self):
        pattern = re.compile(r"videoId.{15}")
        match_list = pattern.findall(str(self.like_data))
        link = r"https://www.youtube.com/watch?v=" + match_list[-1][11:]
        return link, match_list

    def heat_map(self):
        self.debug_print("Generating heatmap...")
        times = self.find_times()
        watch_times = [0 for t in range(12)]
        for time in times:
            if time.weekday() == day:
                watch_times[(time.hour // 2) - time.hour % 2] += 1
        plt.figure(figsize=(20, 5))
        sns.heatmap([watch_times],
                    cmap="Blues",
                    linewidths=2,
                    xticklabels=[],
                    yticklabels=["Watch Times"])
        plt.title("What Time Do You Usually Watch Youtube Videos? (Eastern Standard Time)",
                  fontsize=27,
                  color="steelblue",
                  fontweight="bold",
                  fontname="Arial")
        plt.annotate("The plot above is based on a total of %s videos you have watched" % len(self.find_links()),
                     (0, 0), (0, -20),
                     fontsize=20,
                     color="steelblue",
                     fontweight="bold",
                     fontname="Arial",
                     xycoords="axes fraction",
                     textcoords="offset points",
                     va="top")
        plt.savefig(os.path.join(self.image_dir, "week_heatmap.png"), dpi=400)
        plt.clf()
        self.debug_print("Heatmap generation completed.")

    def table(self):
        self.debug_print("Generating table...")
        plt.figure(figsize=(6, 6))
        plt.title(
            "Do You Still Remember?",
            fontsize=27,
            color="steelblue",
            fontweight="bold",
            fontname="Arial",
        )
        plt.annotate(
            "First Watched Video: \n\nMost Watched Video:\n\nFirst Like"
            "d Video:\n\nFirst Commented Video:\n\nFirst Searched Words:",
            (0, 0),
            (-80, 30),
            fontsize=20,
            color="steelblue",
            fontweight="bold",
            fontname="Arial",
            xycoords="axes fraction",
            textcoords="offset points",
            va="top",
        )
        plt.axis("off")
        plt.savefig(os.path.join(self.image_dir, "info_table.png"), dpi=400)
        plt.clf()
        self.debug_print("Table generation completed.")

    def wordCloud(self):
        self.debug_print("Generating word cloud...")
        search_raw, search_clean = self.search_history()
        words_to_cloud = " ".join(search_clean)
        plt.figure(figsize=(20, 10))
        wordcloud = WordCloud(
            background_color="white",
            width=800,
            height=400,
            max_font_size=200,
            max_words=150,
            contour_color="steelblue",
            contour_width=2,
            collocations=False,
        ).generate(words_to_cloud)
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        plt.savefig(os.path.join(self.image_dir, "search_wordcloud.png"), dpi=400)
        plt.clf()
        self.debug_print("Word cloud generation completed.")

    def json_analysis(self):
        self.debug_print("Generating JSON analysis...")
        like_link, like_list = self.like_history()
        fig, ax = plt.subplots()
        labels, counts = np.unique([like[-1] for like in like_list], return_counts=True)
        ax.pie(counts, labels=labels, autopct="%1.1f%%")
        ax.axis("equal")
        plt.title("What Topics Do You Like the Most on Youtube?",
                  fontsize=25,
                  color="steelblue",
                  fontweight="bold",
                  fontname="Arial")
        plt.savefig(os.path.join(self.image_dir, "like_piechart.png"), dpi=400)
        plt.clf()
        self.debug_print("JSON analysis completed.")

    def generate_report(self):
        self.debug_print("Generating report...")
        self.process_data()
        self.heat_map()
        self.table()
        self.wordCloud()
        self.json_analysis()
        self.debug_print("Report generation completed.")

def main():
    watch_history_file = input("Enter the path to your YouTube watch history HTML file: ")
    search_history_file = input("Enter the path to your YouTube search history HTML file: ")
    comments_history_file = input("Enter the path to your YouTube comments history HTML file: ")
    like_history_file = input("Enter the path to your YouTube like history JSON file: ")
    image_dir = input("Enter the path to the directory where you want to save images: ")

    viz = Visualization(watch_history_file, search_history_file, comments_history_file, like_history_file, image_dir)
    viz.generate_report()

if __name__ == "__main__":
    main()

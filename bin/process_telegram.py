from google_takeout_parser.path_dispatch import TakeoutParser

if __name__ == "__main__":
    directory = "M:/development/data/takeout_google_service_bohdan_hiusak6/Takeout/Chrome"
    tp = TakeoutParser(directory)
    results = list(tp.parse())
    r = tp.dispatch_map()
    for result in results:
        print(result)

    print()
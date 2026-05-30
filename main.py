from models import EmailProcessor
import sys

def main():
    if len(sys.argv) != 3:
        print("Usage: python main.py <input.pst> <output.csv>")
        return

    processor = EmailProcessor(sys.argv[1])
    processor.extract_from_pst()
    processor.filter_and_sort()
    out = processor.save_to_csv(sys.argv[2])
    stats = processor.get_stats()

    print(f"Done! Saved in: {out}")
    print(f"Stats: {stats}")

if __name__ == "__main__":
    main()
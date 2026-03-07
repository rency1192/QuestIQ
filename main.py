import os
os.environ["PYTHONIOENCODING"] = "utf-8"
from scripts.pipeline import Pipeline

if __name__ == "__main__":
    pipeline = Pipeline()
    pipeline.run()
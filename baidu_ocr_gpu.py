# gpu
from paddlex import create_pipeline

pipeline = create_pipeline(pipeline="OCR",device="gpu")

output = pipeline.predict("13200.0.jpg")
for res in output:
    res.print()

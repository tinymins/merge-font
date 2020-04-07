# Merge Font With Code Point Mapping

This project is building for merge ttf font file with custom code point mapping. Basicly, it supply two cp-mapping mode: zh2Hans and zh2Hant.

Assume that you already got two fonts: Font-Hans.ttf for Simplified Chinese, and Font-Hant for Traditional Chinese.

You can simplely input command to merge all Traditional Chinese characters into font file as Simplified Chinese code point:
```
python merge-font.py Font-Hans.ttf Font-Hant.ttf zh2Hans output.ttf
```

In oppsite, you can simplely input command to merge all Simplified Chinese characters into font file as Traditional Chinese code point:
```
python merge-font.py Font-Hant.ttf Font-Hans.ttf zh2Hant output.ttf
```

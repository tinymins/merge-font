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

## Options

### --cmap

You can pass `cmap` version list. By default, all version of cmap will be updated during insertion.

```
--cmap 12
--cmap 4,12
```

### --optimize

You can pass `--optimize` if you want to make your font smaller. This option will remove all empty glyphs from cmap list.

## Notice

Some fonts contains to much code point in low versioned cmap list such as `cmap_format_4`. So font merge may got crashed when trying insert new cmap. If you have this kind of problem, try use `--optimize` option and try again. If the problem is still, try use `--cmap` option to pass specific cmap versions and try again.

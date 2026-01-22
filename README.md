# Font Conv

[中文文档](README.zh-CN.md)

A Python tool for merging TrueType fonts with custom code point mapping, specifically designed for Chinese Simplified/Traditional character conversion. Also supports simple font format conversion (OTF ↔ TTF).

## Features

- **Font Format Conversion**: Convert between OTF and TTF formats
- **Single Font Conversion**: Convert a font to support displaying Simplified Chinese as Traditional (or vice versa)
- **Font Merging**: Merge glyphs from one font into another with code point remapping
- **Multiple Conversion Modes**: Support for various Chinese character mapping modes
- **Flexible cmap Support**: Control which cmap format versions to update

## Requirements

- Python 3.7+
- [fonttools](https://github.com/fonttools/fonttools) (for ttx command)

## Installation

```bash
# Install fonttools for ttx support
pip install fonttools
```

## Usage

### Simple Format Conversion

Convert between OTF and TTF formats without any character mapping:

```bash
python font-conv.py <input_font> [--output output_font]
```

**Examples**:

```bash
# Convert OTF to TTF
python font-conv.py "MyFont.otf" --output "MyFont.ttf"

# Convert with cmap filtering
python font-conv.py "MyFont.otf" --output "MyFont.ttf" --cmap 4,12
```

### Single Font Conversion with Mapping

Convert a single font to support Simplified ↔ Traditional Chinese mapping:

```bash
python font-conv.py <input_font> --mapping <preset> [--output output_font]
```

**Example**: Convert a Traditional Chinese font to display Traditional glyphs when Simplified code points are used:

```bash
# Minimal usage (outputs to MyFont-Traditional_Hant2Hans.ttf)
python font-conv.py "MyFont-Traditional.ttf" --mapping Hant2Hans

# With custom output path
python font-conv.py "MyFont-Traditional.ttf" --mapping Hant2Hans --output "MyFont-TradStyle.ttf"
```

### Font Merging Mode

Merge glyphs from one font into another:

```bash
python font-conv.py <base_font> --source <source_font> --mapping <preset> [--output output_font]
```

### Real-World Example: Creating Full CJK Support Font

Suppose you have a font family with separate Traditional (`MyFont-Traditional.ttf`) and Simplified (`MyFont-Simplified.ttf`) versions. Here's how to create different output variants:

**Step 1: Create a Full version (supports both Simplified and Traditional code points)**

```bash
python font-conv.py "MyFont-Traditional.ttf" --source "MyFont-Simplified.ttf" --mapping Hans --output "MyFont-Full.ttf" --cmap 12
```

This takes the Traditional font as base, and uses `Hans` preset to copy Simplified glyphs from the Simplified font to Simplified code points. Result: Traditional code points show Traditional glyphs, Simplified code points show Simplified glyphs.

**Step 2: Create a Traditional-style version (Traditional glyphs for all code points)**

```bash
python font-conv.py "MyFont-Full.ttx" --source "MyFont-Traditional.ttx" --mapping Hant2Hans --output "MyFont-TradStyle.ttf" --overwrite --cmap 12
```

This overwrites the Simplified glyphs with Traditional glyphs (`Hant2Hans` = Traditional glyphs → Simplified code points). Result: a font that always displays Traditional glyphs, even when the text uses Simplified Chinese code points.

| Output | Description | Use Case |
|--------|-------------|----------|
| `MyFont-Full.ttf` | Simplified → Simplified glyph, Traditional → Traditional glyph | Standard CJK support |
| `MyFont-TradStyle.ttf` | All code points → Traditional glyphs | Users who prefer Traditional style on Simplified Chinese systems |

## Options

### `-m, --mapping <preset>`

Specify the code point mapping preset. If not provided, no mapping is applied (useful for simple format conversion).

| Preset | Description |
|--------|-------------|
| `Hans2Hant` | Map Simplified Chinese glyphs → Traditional Chinese code points |
| `Hant2Hans` | Map Traditional Chinese glyphs → Simplified Chinese code points |
| `Hans` | Copy all Simplified Chinese glyphs to base font |
| `Hant` | Copy all Traditional Chinese glyphs to base font |

**Use Cases**:
- **`Hant2Hans`**: When you have a Traditional Chinese font and want it to display Traditional glyphs even when the text uses Simplified Chinese code points
- **`Hans2Hant`**: When you have a Simplified Chinese font and want it to display Simplified glyphs even when the text uses Traditional Chinese code points

### `-o, --output <font_path>`

Specify the output font path. If not provided:
- With `--mapping`: defaults to `<input>_<mapping>.ttf`
- Without `--mapping`: defaults to `<input>.ttf`

### `-s, --source <font_path>`

Specify the font file to read glyphs from. If not provided, the input font is used as both source and target.

### `--cmap <versions>`

Specify which cmap format versions to update. By default, all cmap formats are processed.

```bash
# Update only cmap format 12
--cmap 12

# Update cmap formats 4 and 12
--cmap 4,12
```

### `--overwrite`

Overwrite existing glyphs in the base font. By default, existing non-empty glyphs are preserved.

### `--optimize`

Remove empty glyphs from cmap tables to reduce file size and avoid potential format limitations.

## Troubleshooting

### cmap Format Errors

Some fonts contain cmap formats (like `cmap_format_0`, `cmap_format_2`, `cmap_format_6`) that only support limited character ranges. If you encounter errors during compilation:

1. Use the `--cmap 4,12` option to only update supported formats
2. Use the `--optimize` option to remove empty glyphs

```bash
python font-conv.py "font.ttf" --mapping Hant2Hans --output "output.ttf" --cmap 4,12 --optimize
```

### Large Font Files

If the output font file is too large, use the `--optimize` flag to remove empty glyph entries from cmap tables.

## How It Works

1. **Parse Fonts**: Convert TTF files to TTX (XML format) using fonttools
2. **Build Glyph Dictionary**: Index glyphs by their Unicode code points
3. **Apply Mapping**: Copy glyphs from source font to target code points based on the selected mode
4. **Update Tables**: Update glyf, cmap, hmtx, vmtx, and GlyphOrder tables
5. **Compile Output**: Convert the modified TTX back to TTF format

## License

MIT License

## Author

Emil Zhai

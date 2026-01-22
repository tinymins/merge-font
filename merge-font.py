# -*- coding: utf-8 -*-

'''
    File name: merge-font.py
    Author: Emil Zhai
    Python Version: 3.7
'''

import xml.etree.ElementTree as ET
import copy, os, argparse

from cp_map import Hans, Hant, Hans2Hant, Hant2Hans

MAX_CODE = 0xffff

def find_child(node, tag, name):
  for child in node.findall(tag):
    if child.attrib['name'] == name:
      return child

def replace_child(node, child):
  c = find_child(node, child.tag, child.attrib['name'])
  if c is not None:
    c.attrib = copy.deepcopy(child.attrib)
  else:
    node.append(child)

def copy_child_to_node(node, tag, name, new_name, dst_node):
  if node is None or dst_node is None:
    return
  c = find_child(node, tag, name)
  if c is not None:
    c = copy.deepcopy(c)
    c.set('name', new_name)
    replace_child(dst_node, c)

def remove_child(node, tag, name):
  for c in node.findall(tag):
    if c.attrib['name'] == name:
      node.remove(c)

def merge_font(base_file, merge_file, merge_cp_map, cmap_versions, overwrite_exist, out_file, optimize_size):
  cmap_tags = []
  for i in cmap_versions:
    cmap_tags.append('cmap_format_%s' % str(i))

  base_tree = ET.parse(base_file)
  base_root = base_tree.getroot()
  base_glyf = base_root.find('glyf')
  base_cmap = base_root.find('cmap')
  base_hmtx = base_root.find('hmtx')
  base_vmtx = base_root.find('vmtx')
  base_glyph_order = base_root.find('GlyphOrder')
  base_glyph_order_max = 0
  base_glyf_dict = {}

  merge_tree = ET.parse(merge_file)
  merge_root = merge_tree.getroot()
  merge_glyf = merge_root.find('glyf')
  merge_cmap = merge_root.find('cmap')
  merge_hmtx = merge_root.find('hmtx')
  merge_vmtx = merge_root.find('vmtx')
  merge_glyf_dict = {}

  for glyph in base_glyf.findall('TTGlyph'):
    name = glyph.attrib['name'].lower()
    if name.startswith('uni'):
      base_glyf_dict[name[3:]] = glyph

  for glyph in merge_glyf.findall('TTGlyph'):
    name = glyph.attrib['name'].lower()
    if name.startswith('uni'):
      merge_glyf_dict[name[3:]] = glyph

  for glyph in base_glyph_order.findall('GlyphID'):
    base_glyph_order_max = max(base_glyph_order_max, int(glyph.attrib['id']))

  base_cmaps = []
  for cmap in base_cmap.findall('*'):
    if cmap.tag.startswith('cmap_format_'):
      if cmap.tag in cmap_tags:
        base_cmaps.append(cmap)
      else:
        base_cmap.remove(cmap)

  for src_code in merge_cp_map:
    dst_code = merge_cp_map[src_code]
    if dst_code > MAX_CODE:
      continue
    src_code = '%04x' % src_code
    dst_code = '%04x' % dst_code

    # check if src code exists in merge ttx
    if src_code not in merge_glyf_dict:
      continue
    if dst_code in base_glyf_dict and not overwrite_exist and len(base_glyf_dict[dst_code]) > 0:
      continue
    name = 'uni' + src_code.upper()
    new_name = 'uni' + dst_code.upper()

    # dealing with glyph
    glyf = copy.deepcopy(merge_glyf_dict[src_code])
    glyf.set('name', new_name)
    if dst_code in base_glyf_dict:
      # if dst code exists in base ttx, just replace its glyph
      base_glyf_dict[dst_code].clear()
      base_glyf_dict[dst_code].attrib = glyf.attrib
      for c in glyf:
        base_glyf_dict[dst_code].append(c)
    else:
      # or create new glyph and append it
      base_glyf.append(glyf)
      base_glyf_dict[dst_code] = glyf
      glyph_order = ET.Element('GlyphID')
      glyph_order.set('id', str(base_glyph_order_max + 1))
      glyph_order.set('name', new_name)
      base_glyph_order.append(glyph_order)
      base_glyph_order_max = base_glyph_order_max + 1

    # dealing with cmaps
    for cmap in base_cmaps:
      node = ET.Element('map')
      node.set('code', '0x' + dst_code)
      node.set('name', new_name)
      replace_child(cmap, node)

    # dealing with v and h mtx
    copy_child_to_node(merge_hmtx, 'mtx', name, new_name, base_hmtx)
    copy_child_to_node(merge_vmtx, 'mtx', name, new_name, base_vmtx)

  # remove empty glyphs, because some cmap only supports max length 65535
  if optimize_size:
    for glyph in base_glyf.findall('TTGlyph'):
      if len(glyph) == 0 and glyph.attrib['name'] != 'uni0000' and glyph.attrib['name'].startswith('uni'):
        name = glyph.attrib['name']
        for cmap in base_cmaps:
          remove_child(cmap, 'map', name)
        # base_glyf.remove(glyph)
        # remove_child(base_hmtx, 'mtx', name)
        # remove_child(base_vmtx, 'mtx', name)
        # remove_child(base_glyph_order, 'GlyphID', name)

  base_tree.write(out_file, xml_declaration=True, encoding="UTF-8")

# Preset name mapping
PRESET_MAP = {
  'Hans2Hant': Hans2Hant,
  'Hant2Hans': Hant2Hans,
  'Hans': Hans,
  'Hant': Hant,
}

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description='Merge TrueType fonts with Chinese Simplified/Traditional code point mapping.',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog='''
Examples:
  %(prog)s Hant2Hans "font.ttf"
  %(prog)s Hant2Hans "font.ttf" -o "output.ttf"
  %(prog)s Hant2Hans "base.ttf" -s "source.ttf" -o "merged.ttf"
'''
  )
  parser.add_argument('preset', choices=['Hans2Hant', 'Hant2Hans', 'Hans', 'Hant'],
                      help='code point mapping preset: Hans2Hant (Simplified->Traditional), Hant2Hans (Traditional->Simplified), Hans/Hant (copy glyphs)')
  parser.add_argument('input', help='path to input font file')
  parser.add_argument('-o', '--output', dest='output_path', help='path to output font (default: <input>_<preset>.ttf)', default=None)
  parser.add_argument('-s', '--source', dest='source_path', help='font file to read glyphs from (default: same as input)', default=None)
  parser.add_argument('--cmap', help='cmap versions to update (default: all). Example: --cmap 4,12', default='')
  parser.add_argument('--overwrite', action='store_true', help='overwrite existing glyphs in base font')
  parser.add_argument('--optimize', action='store_true', help='optimize file size by removing empty glyphs from cmap')
  args = parser.parse_args()

  # Generate default output path based on input filename
  if args.output_path is None:
    input_name, input_ext = os.path.splitext(args.input)
    args.output_path = '%s_%s%s' % (input_name, args.preset, input_ext if input_ext else '.ttf')

  # If source_path is not specified, use input (single font conversion mode)
  if args.source_path is None:
    args.source_path = args.input

  is_same_source = (args.input == args.source_path)

  if is_same_source:
    print('--------------------------------------------------')
    print('Single font conversion mode: %s' % args.input)
  else:
    print('--------------------------------------------------')
    print('Merging glyphs from %s to %s' % (args.source_path, args.input))

  base_filename, base_fileext = os.path.splitext(args.input)
  if base_fileext.lower() != '.ttx':
    print('--------------------------------------------------')
    print('Parsing input font to ttx...')
    if os.path.exists(base_filename + '.ttx'):
      os.remove(base_filename + '.ttx')
    os.system('ttx ' + args.input)

  source_filename, source_fileext = os.path.splitext(args.source_path)
  # Only parse source font if it's different from input font
  if not is_same_source and source_fileext.lower() != '.ttx':
    print('--------------------------------------------------')
    print('Parsing source font to ttx...')
    if os.path.exists(source_filename + '.ttx'):
      os.remove(source_filename + '.ttx')
    os.system('ttx ' + args.source_path)

  print('--------------------------------------------------')
  print('Prepare for merging font with code point map...')
  output_filename, output_fileext = os.path.splitext(args.output_path)
  if os.path.exists(output_filename + '.ttx'):
    os.remove(output_filename + '.ttx')
  if os.path.exists(output_filename + '.ttf'):
    os.remove(output_filename + '.ttf')

  cp_map = PRESET_MAP[args.preset]

  # Check for problematic cmap formats (format 0 only supports 0-255)
  if args.cmap == '':
    base_ttx = base_filename + '.ttx'
    problematic_formats = []
    try:
      import xml.etree.ElementTree as ET
      tree = ET.parse(base_ttx)
      root = tree.getroot()
      cmap = root.find('cmap')
      if cmap is not None:
        for child in cmap:
          if child.tag == 'cmap_format_0':
            problematic_formats.append('0')
          elif child.tag == 'cmap_format_2':
            problematic_formats.append('2')
          elif child.tag == 'cmap_format_6':
            problematic_formats.append('6')
      if problematic_formats:
        print('--------------------------------------------------')
        print('WARNING: Font contains cmap format(s) %s which only support limited character range.' % ', '.join(problematic_formats))
        print('This may cause errors when compiling the output font.')
        print('Please use --cmap 4,12 to avoid this issue.')
        print('Example: python merge-font.py %s "%s" -o "%s" --cmap 4,12' % (args.preset, args.input, args.output_path))
        print('--------------------------------------------------')
        user_input = input('Continue anyway? (y/N): ').strip().lower()
        if user_input != 'y':
          print('Aborted.')
          exit(1)
    except Exception as e:
      pass  # If check fails, continue anyway

  if args.cmap == '':
    cmap_versions = range(32)
  else:
    cmap_versions = args.cmap.split(',')

  merge_font(base_filename + '.ttx', source_filename + '.ttx', cp_map, cmap_versions, args.overwrite, output_filename + '.ttx', args.optimize)

  print('--------------------------------------------------')
  print('Prepare for parsing output font file...')
  os.system('ttx ' + output_filename + '.ttx')

  print('--------------------------------------------------')
  print('Finished with output file %s' % args.output_path)

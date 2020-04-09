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
    for i in cmap_versions:
      for cmap in base_cmap.findall('cmap_format_%d' % i):
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
        for i in range(32):
          for cmap in base_cmap.findall('cmap_format_%d' % i):
            remove_child(cmap, 'map', name)
        # base_glyf.remove(glyph)
        # remove_child(base_hmtx, 'mtx', name)
        # remove_child(base_vmtx, 'mtx', name)
        # remove_child(base_glyph_order, 'GlyphID', name)

  base_tree.write(out_file, xml_declaration=True, encoding="UTF-8")

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Process some integers.')
  parser.add_argument('base_path', help='path to base font')
  parser.add_argument('merge_path', help='path to merge font where you want to read font(s) and append to base font')
  parser.add_argument('mode', choices=['Hans', 'Hant', 'Hans2Hant', 'Hant2Hans'])
  parser.add_argument('output_path', help='path to output font')
  parser.add_argument('--cmap', help='cmap versions (default: all cmaps)', default=range(32))
  parser.add_argument('--overwrite', action='store_true', help='overwrite exist characters')
  parser.add_argument('--optimize', action='store_true', help='optimize font file size, remove empty glyph from cmap')
  args = parser.parse_args()

  base_filename, base_fileext = os.path.splitext(args.base_path)
  if base_fileext.lower() != '.ttx':
    print('--------------------------------------------------')
    print('Prepare for parsing base font file to ttx...')
    if os.path.exists(base_filename + '.ttx'):
      os.remove(base_filename + '.ttx')
    os.system('ttx ' + args.base_path)

  merge_filename, merge_fileext = os.path.splitext(args.merge_path)
  if merge_fileext.lower() != '.ttx':
    print('--------------------------------------------------')
    print('Prepare for parsing merge font file to ttx...')
    if os.path.exists(merge_filename + '.ttx'):
      os.remove(merge_filename + '.ttx')
    os.system('ttx ' + args.merge_path)

  print('--------------------------------------------------')
  print('Prepare for merging font with code point map...')
  output_filename, output_fileext = os.path.splitext(args.output_path)
  if os.path.exists(output_filename + '.ttx'):
    os.remove(output_filename + '.ttx')
  if os.path.exists(output_filename + '.ttf'):
    os.remove(output_filename + '.ttf')

  if args.mode == 'Hans':
    cp_map = Hans
  elif args.mode == 'Hant':
    cp_map = Hant
  elif args.mode == 'Hans2Hant':
    cp_map = Hans2Hant
  elif args.mode == 'Hant2Hans':
    cp_map = Hant2Hans
  merge_font(base_filename + '.ttx', merge_filename + '.ttx', cp_map, args.cmap, args.overwrite, output_filename + '.ttx', args.optimize)

  print('--------------------------------------------------')
  print('Prepare for parsing output font file...')
  os.system('ttx ' + output_filename + '.ttx')

  print('--------------------------------------------------')
  print('Finished...')

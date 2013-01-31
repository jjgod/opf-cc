#!/usr/bin/env python
# Convert files in Open Packaging Format from Traditional Chinese
# to Simplified Chinese.

import sys, os, zipfile, re, codecs, subprocess, glob, shutil
import opencc
import mobiunpack
import kindlestrip
import lxml
from lxml.html import parse

debug = True
fsenc = sys.getfilesystemencoding()

def find_paths(converter):
    input_path = sys.argv[1]

    if not os.path.exists(input_path):
        print "%s does not exist." % input_path
        sys.exit(1)

    ext = os.path.splitext(input_path)[1]
    if not ext in [".epub", ".mobi"] or os.path.isdir(input_path):
        print "%s is not a valid input file." % input_path
        sys.exit(1)

    output_file_path = converter.convert(input_path)

    output_path = find_output_path(input_path)
    if not (debug and os.path.isdir(output_path)):
        print "Try extracting %s to %s" % (input_path, output_path)
        if ext == ".epub":
            zf = zipfile.ZipFile(input_path)
            zf.extractall(output_path)
        else:
            # Otherwise it's a mobi, use mobiunpack
            mobiunpack.unpackBook(input_path, output_path)

    return (input_path, output_path, output_file_path)

def find_output_path(input_path):
    candidate = os.path.splitext(input_path)[0]
    if os.path.exists(candidate):
        # Quick shortcut for debugging, do not attempt to extract
        # the file again, reuse the extracted directory.
        if debug and os.path.isdir(candidate):
            return candidate
        match = re.match('(.*)-(\d+)', candidate)
        if match:
            print match.group(1)
            candidate = match.group(1)
            digit = int(match.group(2)) + 1
        else:
            digit = 1
        candidate = "%s-%d" % (candidate, digit)
        return find_output_path(candidate)
    return candidate

def find_opf_path(input_path):
    metadata_file = os.path.join(input_path, "META-INF", "container.xml")
    if os.path.isfile(metadata_file):
        metadata = lxml.etree.parse(metadata_file)
        for root_file in metadata.iter('rootfile'):
            opf_file = root_file.attrib['full-path']
            opf_path = os.path.join(input_path, opf_file)
            if os.path.isfile(opf_path):
                return opf_path
    else:
        # Otherwise it's not in Open Container Format, look for opf in
        # the hard way
        opfs = glob.glob(os.path.join(input_path, '*.opf'))
        if len(opfs):
            return opfs[0]
    return None

def find_files_to_convert(input_path, opf_path):
    opf = parse(opf_path)
    files = [opf_path]
    types = ['application/x-dtbncx+xml', 'application/xhtml+xml', 'text/x-oeb1-document']
    for item in opf.iter('item'):
        media_type = item.attrib['media-type']
        if media_type in types:
            href = item.attrib['href']
            path = os.path.join(input_path, href.encode(fsenc))
            if os.path.isfile(path):
                files.append(path)
    return files

def convert_files_in_place(converter, files):
    for f in files:
        print 'Converting file: %s' % f
        ext = os.path.splitext(f)[1]
        if ext == '.ncx':
            ncx = lxml.etree.parse(f)
            for text in ncx.iter('text'):
                text.text = converter.convert(text.text.encode('utf-8')).decode('utf-8')
            ncx.write(f, encoding='utf-8', xml_declaration=True, pretty_print=True)
        elif ext == '.opf':
            # Quick and dirty way to convert metadata because lxml.html doesn't work
            opf = open(f)
            opf_contents = opf.read().split('</metadata>')
            opf.close()
            opf_contents[0] = converter.convert(opf_contents[0])
            opf = open(f, 'w')
            opf.write('</metadata>'.join(opf_contents))
            opf.close()
        else:
            output_file = '%s.tmp' % f
            cmd = "opencc -i '%s' -o '%s' -c zht2zhs.ini" % (f, output_file)
            os.system(cmd)
            os.rename(output_file, f)

def add_dir_to_zip(archive, base, current):
    for f in os.listdir(os.path.join(base, current)):
        filename = os.path.join(current, f)
        fullname = os.path.join(base, filename)
        if os.path.isdir(fullname):
            add_dir_to_zip(archive, base, filename)
        else:
            archive.write(fullname, filename)

def repack_files(input_path, output_file_path, opf_path):
    (trunk, ext) = os.path.splitext(output_file_path)
    if os.path.isfile(output_file_path):
        old_file_path = "%s.old%s" % (trunk, ext)
        print "Renaming existing file to %s" % old_file_path
        os.rename(output_file_path, old_file_path)
    print "Repacking converted files into %s" % output_file_path
    if ext == '.epub':
        # epub is just normal zip file with a special extension
        cmd_args = ['zip', '-r', output_file_path, '.']
        epub = zipfile.ZipFile(output_file_path, "w", zipfile.ZIP_DEFLATED)
        add_dir_to_zip(epub, input_path, '.')
        epub.close()
    else:
        # Otherwise it's a mobi file, use kindlegen to repack
        cmd_args = []
        output_file = os.path.basename(output_file_path)
        cmd_args = ['kindlegen', opf_path, '-c2', '-verbose', '-o', output_file]
        p = subprocess.Popen(cmd_args, cwd=input_path)
        p.wait()

    if ext == '.mobi':
        # KindleGen puts output file under the same directory as the input file.
        original_output_path = os.path.join(input_path,
                               os.path.basename(output_file_path))
        # KindleGen introduced redundant data, use kindlestrip to remove that.
        data_file = file(original_output_path, 'rb').read()
        strippedFile = kindlestrip.SectionStripper(data_file)
        outf = file(output_file_path, 'wb')
        outf.write(strippedFile.getResult())
        outf.close()

    print "Removing temporary directory %s" % input_path
    shutil.rmtree(input_path)

if len(sys.argv) < 2:
    print "usage: %s <book.epub|book.mobi>"
    sys.exit(1)

with opencc.OpenCC(config="zht2zhs.ini") as converter:
    for path in ['trad_to_simp_characters.ocd',
                 'trad_to_simp_phrases.ocd']:
        converter.dict_load(path, opencc.DictType.DATRIE)
    (input_file_path, extracted_path, output_file_path) = find_paths(converter)
    opf_path = find_opf_path(extracted_path)

    if opf_path:
        files = find_files_to_convert(extracted_path, opf_path)
        if len(files):
            convert_files_in_place(converter, files)
        repack_files(extracted_path, output_file_path, opf_path)
    else:
        print "%s is not in Open Packaging Format, abort." % extracted_path
        sys.exit(1)


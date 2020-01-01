# -*- coding: utf-8 -*-
import csv
import errno
import importlib
import io
import operator
import os
import re

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from . import readability_ui
from .morphemes import Morpheme, MorphDb, getMorphemes, altIncludesMorpheme
from .morphemizer import getMorphemizerByName
from .util import mw
from .preferences import get_preference as cfg

importlib.reload(readability_ui)


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    """
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    """
    return [atoi(c) for c in re.split(r'(\d+)', text)]


class Source:
    def __init__(self, name, morphs, unknown_db):
        self.name = os.path.basename(name)
        self.morphs = morphs
        self.unknown_db = unknown_db


def getPath(le, caption, open_directory=False):  # LineEdit -> GUI ()
    start_path = os.path.dirname(le.text())
    if start_path == '':
        start_path = cfg('path_dbs')

    try:
        if open_directory:
            path = QFileDialog.getExistingDirectory(caption=caption, directory=start_path,
                                                    options=QFileDialog.ShowDirsOnly)
        else:
            path = QFileDialog.getOpenFileName(caption=caption, directory=start_path)[0]
    except:
        return

    if path:
        le.setText(path)


# Todo: Use a normal DB with file locations.
class CountingMorphDB:
    def __init__(self):
        self.db = {}

    def addMorph(self, m, count):
        gk = m.getGroupKey()
        if gk not in self.db:
            self.db[gk] = {}
        ms = self.db[gk]
        if m not in ms:
            ms[m] = [0, False]
        ms[m][0] += count

    def getTotalNormMorphs(self):
        return len(self.db)

    def getTotalVariationMorphs(self):
        return sum([len(ms) for ms in self.db.values()])

    def getFuzzyCount(self, m):
        gk = m.getGroupKey()
        if gk not in self.db:
            return 0
        count = 0
        ms = self.db[gk]
        for alt, c in ms.items():
            if c[1]:  # Skip marked morphs
                continue
            if altIncludesMorpheme(alt, m):  # pylint: disable=W1114 #ToDo: verify if pylint is right
                count += c[0]
        return count


class MorphMan(QDialog):
    def __init__(self, parent=None):
        super(MorphMan, self).__init__(parent)
        self.mw = parent
        self.ui = readability_ui.Ui_ReadabilityDialog()
        self.ui.setupUi(self)

        # Init morphemizer
        self.morphemizer = getMorphemizerByName(cfg('default_morphemizer'))

        # Status bar
        self.ui.statusBar = QStatusBar(self)
        self.ui.verticalLayout.addWidget(self.ui.statusBar)
        self.ui.morphemizerLabel = QLabel(self)
        self.ui.morphemizerLabel.setText(
            'Dictionary: %s %s' % (self.morphemizer.getDescription(), self.morphemizer.getDictionary()))
        self.ui.morphemizerLabel.setMargin(6)
        self.ui.statusBar.addWidget(self.ui.morphemizerLabel)

        # Default settings
        self.ui.inputPathEdit.setText(cfg('path_analysis_input'))
        self.ui.inputPathButton.clicked.connect(
            lambda le: getPath(self.ui.inputPathEdit, "Select Input Directory", True))
        self.ui.masterFreqEdit.setText(cfg('path_master_frequency_list'))
        self.ui.masterFreqButton.clicked.connect(
            lambda le: getPath(self.ui.masterFreqEdit, "Select Master Frequency List"))
        self.ui.knownMorphsEdit.setText(cfg('path_known'))
        self.ui.knownMorphsButton.clicked.connect(lambda le: getPath(self.ui.knownMorphsEdit, "Select Known Morphs DB"))
        self.ui.outputFrequencyEdit.setText(cfg('path_dbs'))
        self.ui.outputFrequencyButton.clicked.connect(
            lambda le: getPath(self.ui.outputFrequencyEdit, "Select Output Directory", True))
        self.ui.targetSpinBox.setProperty("value", cfg('default_study_target'))

        # Connect buttons
        self.ui.analyzeButton.clicked.connect(lambda le: self.onAnalyze())
        self.ui.closeButton.clicked.connect(lambda le: self.close())

        # Output text font
        doc = self.ui.outputText.document()
        font = doc.defaultFont()
        font.setFamily("Courier New")
        doc.setDefaultFont(font)

    def clearOutput(self):
        self.ui.outputText.clear()

    def writeOutput(self, m):
        self.ui.outputText.moveCursor(QTextCursor.End)
        self.ui.outputText.insertPlainText(m)

    def onAnalyze(self):
        self.clearOutput()

        input_path = self.ui.inputPathEdit.text()
        readability_target = float(self.ui.targetSpinBox.value())
        master_freq_path = self.ui.masterFreqEdit.text()
        known_words_path = self.ui.knownMorphsEdit.text()
        output_path = self.ui.outputFrequencyEdit.text()
        save_frequency_list = self.ui.frequencyListCheckBox.isChecked()
        save_word_report = self.ui.wordReportCheckBox.isChecked()
        save_study_plan = self.ui.studyPlanCheckBox.isChecked()

        if not os.path.exists(output_path):
            try:
                os.makedirs(output_path)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

        frequency_list_path = os.path.normpath(output_path + '/frequency.txt')
        word_report_path = os.path.normpath(output_path + '/word_freq_report.txt')
        study_plan_path = os.path.normpath(output_path + '/study_plan.txt')

        master_db = CountingMorphDB()
        unknown_db = CountingMorphDB()

        master_total_instances = 0
        master_current_score = 0
        master_weight = 1.0

        all_morphs = {}

        if os.path.isfile(master_freq_path):
            with io.open(master_freq_path, encoding='utf-8-sig') as csvfile:
                csvreader = csv.reader(csvfile, delimiter="\t")
                for row in csvreader:
                    try:
                        instances = int(row[0])
                        m = Morpheme(row[1], row[2], row[2], row[3], row[4], row[5])

                        master_db.addMorph(m, instances)
                        master_total_instances += instances
                    except:
                        pass
            self.writeOutput("Master morphs loaded: K %d V %d\n" % (
                master_db.getTotalNormMorphs(), master_db.getTotalVariationMorphs()))
        else:
            print("Master frequency file '%s' not found" % master_freq_path)

        if os.path.isfile(known_words_path):
            known_db = MorphDb(known_words_path, ignoreErrors=True)

            total_k = len(known_db.groups)
            total_v = len(known_db.db)
            self.writeOutput("Known morphs loaded: K %d V %d\n" % (total_k, total_v))
        else:
            self.writeOutput("Known words DB '%s' not found\n" % known_words_path)

        if master_total_instances > 0:
            master_current_score = 0
            for ms in master_db.db.values():
                for m, c in ms.items():
                    if known_db.matches(m):
                        master_current_score += c[0]
                        c[1] = True  # mark matched
            self.writeOutput("\n[Current master frequency readability] %0.02f\n" % (
                    master_current_score * 100.0 / master_total_instances))

        sources = []

        def measure_readability(file_name, is_ass, is_srt):
            i_count = 0
            known_count = 0
            seen_morphs = {}
            known_morphs = {}
            source_unknown_db = CountingMorphDB()

            def proc_lines(text, is_ass, is_srt):
                text_index = -1
                num_fields = 1
                srt_count = 0

                def parse_text(text):
                    nonlocal i_count, known_count, seen_morphs, known_morphs, all_morphs

                    parsed_morphs = getMorphemes(self.morphemizer, text)
                    for m in parsed_morphs:
                        # Count morph for word report
                        all_morphs[m] = all_morphs.get(m, 0) + 1

                        seen_morphs[m] = seen_morphs.get(m, 0) + 1
                        i_count += 1
                        if known_db.matches(m):
                            known_morphs[m] = known_morphs.get(m, 0) + 1
                            known_count += 1
                        else:
                            unknown_db.addMorph(m, 1)
                            source_unknown_db.addMorph(m, 1)

                filtered_text = ''
                for t in text.split('\n'):
                    if is_ass:
                        if 'Format:' in t:
                            formats = [x.strip() for x in t[8:].split(',')]
                            if 'Text' in formats:
                                text_index = formats.index('Text')
                                num_fields = len(formats)
                            else:
                                text_index = -1
                            continue
                        elif ('Dialogue:' not in t) or (text_index < 0):
                            continue
                        t = t[9:].split(',', num_fields)
                        t = t[text_index]
                    elif is_srt:
                        srt_count += 1
                        if srt_count <= 2:
                            continue
                        elif t == '':
                            srt_count = 0
                            continue
                    filtered_text += t + '\n'
                    if len(filtered_text) >= 2048:
                        parse_text(filtered_text)
                        filtered_text = ''

                parse_text(filtered_text)

            try:
                with open(file_name.strip(), 'rt', encoding='utf-8') as f:
                    input = '\n'.join([l.strip().replace(u'\ufeff', '') for l in f.readlines()])
                    proc_lines(input, is_ass, is_srt)
                    source = Source(file_name, seen_morphs, source_unknown_db)
                    readability = 0.0 if i_count == 0 else 100.0 * known_count / i_count
                    known_percent = 0.0 if len(seen_morphs.keys()) == 0 else 100.0 * len(known_morphs) / len(
                        seen_morphs.keys())
                    self.writeOutput('%s\t%d\t%d\t%0.2f\t%d\t%d\t%0.2f\n' % (
                        source.name, len(seen_morphs), len(known_morphs), known_percent, i_count, known_count,
                        readability))

                    if save_study_plan:
                        sources.append(source)
            except:
                self.writeOutput("Failed to process '%s'\n" % file_name)
                raise

        def accepted_filetype(filename):
            return filename.lower().endswith(('.srt', '.ass', '.txt'))

        list_of_files = list()
        for (dirpath, _, filenames) in os.walk(input_path):
            list_of_files += [os.path.join(dirpath, filename) for filename in filenames if accepted_filetype(filename)]

        if len(list_of_files) > 0:
            self.writeOutput('%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
                "Input", "Total Morphs", "Known Morphs", "% Known Morphs", "Total Instances", "Known Instances",
                "% Readability"))

            mw.progress.start(label='Updating data', max=len(list_of_files), immediate=True)
            for n, file_path in enumerate(sorted(list_of_files, key=natural_keys)):
                mw.progress.update(value=n, label='Parsing (%d/%d) %s' % (
                    n + 1, len(list_of_files), os.path.basename(file_path)))
                if os.path.isfile(file_path):
                    is_ass = os.path.splitext(file_path)[1].lower() == '.ass'
                    is_srt = os.path.splitext(file_path)[1].lower() == '.srt'
                    measure_readability(file_path, is_ass, is_srt)
            mw.progress.finish()
        else:
            self.writeOutput('\nNo files found to process.\n')
            return

        if save_word_report:
            self.writeOutput("\n[Saving word report to '%s'...]\n" % word_report_path)
            with open(word_report_path, 'wt', encoding='utf-8') as f:
                last_count = 0
                morph_idx = 0
                group_idx = 0
                morph_total = 0.0
                all_morphs_count = sum(n for n in all_morphs.values())

                for m in sorted(all_morphs.items(), key=operator.itemgetter(1), reverse=True):
                    if m[1] != last_count:
                        last_count = m[1]
                        group_idx += 1
                    morph_idx += 1
                    morph_delta = 100.0 * m[1] / all_morphs_count
                    morph_total += morph_delta
                    print('%d\t%s\t%s\t%s\t%s\t%s\t%d\t%d\t%0.8f\t%0.8f' % (
                        m[1], m[0].norm, m[0].base, m[0].read, m[0].pos, m[0].subPos, group_idx, morph_idx, morph_delta,
                        morph_total), file=f)

        learned_tot = 0
        learned_morphs = []

        all_missing_morphs = []

        if save_study_plan:
            self.writeOutput("\n[Saving Study Plan to '%s'...]\n" % study_plan_path)
            with open(study_plan_path, 'wt', encoding='utf-8') as f:
                for n, s in enumerate(sources):
                    known_i = 0
                    seen_i = 0
                    learned_m = 0
                    missing_morphs = []

                    for m in s.morphs.items():
                        seen_i += m[1]
                        morph = m[0]
                        if known_db.matches(morph):
                            known_i += m[1]
                        else:
                            source_unknown_count = s.unknown_db.getFuzzyCount(morph)
                            unknown_count = unknown_db.getFuzzyCount(morph)
                            master_count = master_db.getFuzzyCount(morph)

                            score = source_unknown_count * 600 + unknown_count * 600 + master_count * master_weight
                            missing_morphs.append((m[0], source_unknown_count, unknown_count, master_count, score))

                    all_missing_morphs += missing_morphs

                    if seen_i > 0:
                        readability = known_i * 100.0 / seen_i
                    else:
                        readability = 100.0
                    readability_0 = readability

                    learned_this_source = []

                    for m in sorted(missing_morphs, key=operator.itemgetter(4), reverse=True):
                        if readability >= readability_target:
                            break

                        known_db.addMLs1(m[0], set())
                        learned_morphs.append(m)
                        learned_this_source.append(m)
                        known_i += m[1]
                        learned_m += 1
                        readability = known_i * 100.0 / seen_i

                    learned_tot += learned_m
                    source_str = "'%s' study goal: (%3d/%4d) readability: %0.2f -> %0.2f\n" % (
                        s.name, learned_m, learned_tot, readability_0, readability)
                    self.writeOutput(source_str)
                    f.write(source_str)

                    for idx, m in enumerate(learned_this_source):
                        f.write('\t' + m[0].show() + '\t[ep_freq %s all_freq %s master_freq %d]\n' % (m[1], m[2], m[3]))

                if save_frequency_list:
                    self.writeOutput("\n[Saving frequency list to '%s'...]\n" % frequency_list_path)
                    with open(frequency_list_path, 'wt', encoding='utf-8') as f:
                        unique_set = set()
                        # First output morphs according to the plan.
                        for m in learned_morphs:
                            if m[0].base in unique_set:
                                continue
                            unique_set.add(m[0].base)
                            print(m[0].base + '\t[ep_freq %s all_freq %s master_freq %d]' % (m[1], m[2], m[3]), file=f)

                        # Followed by all remaining morphs sorted by score.
                        for m in sorted(all_missing_morphs, key=operator.itemgetter(4), reverse=True):
                            if m[0].base in unique_set:
                                continue
                            unique_set.add(m[0].base)
                            print(m[0].base + '\t[ep_freq %s all_freq %s master_freq %d]' % (m[1], m[2], m[3]), file=f)

                if master_total_instances > 0:
                    master_score = 0
                    for ms in master_db.db.values():
                        for m, c in ms.items():
                            if known_db.matches(m):
                                master_score += c[0]
                                c[1] = True  # mark matched
                    self.writeOutput("\n[New master frequency readability] %0.02f -> %0.02f\n" % (
                        master_current_score * 100.0 / master_total_instances,
                        master_score * 100.0 / master_total_instances))


def main():
    mw.mm = MorphMan(mw)
    mw.mm.show()

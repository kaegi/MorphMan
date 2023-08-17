# Form implementation generated from reading ui file 'morph/readability_settings.ui'
#
# Created by: PyQt6 UI code generator 6.4.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


try:
    from PyQt6 import QtCore, QtGui, QtWidgets
except:
    from PyQt5 import QtCore, QtGui, QtWidgets
    QtCore.Qt.AlignmentFlag.AlignLeading = QtCore.Qt.AlignLeading
    QtCore.Qt.AlignmentFlag.AlignTrailing = QtCore.Qt.AlignTrailing


class Ui_ReadabilitySettingsDialog(object):
    def setupUi(self, ReadabilitySettingsDialog):
        ReadabilitySettingsDialog.setObjectName("ReadabilitySettingsDialog")
        ReadabilitySettingsDialog.resize(346, 426)
        ReadabilitySettingsDialog.setSizeGripEnabled(False)
        ReadabilitySettingsDialog.setModal(True)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(ReadabilitySettingsDialog)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.studyPlanGroup = QtWidgets.QGroupBox(ReadabilitySettingsDialog)
        self.studyPlanGroup.setObjectName("studyPlanGroup")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.studyPlanGroup)
        self.verticalLayout.setObjectName("verticalLayout")
        self.alwaysAddMinimumFreqCheckBox = QtWidgets.QCheckBox(self.studyPlanGroup)
        self.alwaysAddMinimumFreqCheckBox.setMinimumSize(QtCore.QSize(0, 0))
        self.alwaysAddMinimumFreqCheckBox.setObjectName("alwaysAddMinimumFreqCheckBox")
        self.verticalLayout.addWidget(self.alwaysAddMinimumFreqCheckBox)
        self.alwaysMeetReadTargettCheckBox = QtWidgets.QCheckBox(self.studyPlanGroup)
        self.alwaysMeetReadTargettCheckBox.setMinimumSize(QtCore.QSize(0, 0))
        self.alwaysMeetReadTargettCheckBox.setObjectName("alwaysMeetReadTargettCheckBox")
        self.verticalLayout.addWidget(self.alwaysMeetReadTargettCheckBox)
        self.resetLearnedAfterEachInputCheckBox = QtWidgets.QCheckBox(self.studyPlanGroup)
        self.resetLearnedAfterEachInputCheckBox.setObjectName("resetLearnedAfterEachInputCheckBox")
        self.verticalLayout.addWidget(self.resetLearnedAfterEachInputCheckBox)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetDefaultConstraint)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.optimalMasterTargetLabel = QtWidgets.QLabel(self.studyPlanGroup)
        self.optimalMasterTargetLabel.setMinimumSize(QtCore.QSize(0, 0))
        self.optimalMasterTargetLabel.setObjectName("optimalMasterTargetLabel")
        self.horizontalLayout.addWidget(self.optimalMasterTargetLabel)
        self.optimalMasterTargetSpinBox = QtWidgets.QDoubleSpinBox(self.studyPlanGroup)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.optimalMasterTargetSpinBox.sizePolicy().hasHeightForWidth())
        self.optimalMasterTargetSpinBox.setSizePolicy(sizePolicy)
        self.optimalMasterTargetSpinBox.setMinimumSize(QtCore.QSize(0, 0))
        self.optimalMasterTargetSpinBox.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.optimalMasterTargetSpinBox.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.optimalMasterTargetSpinBox.setPrefix("")
        self.optimalMasterTargetSpinBox.setMinimum(0.0)
        self.optimalMasterTargetSpinBox.setMaximum(100.0)
        self.optimalMasterTargetSpinBox.setProperty("value", 0.0)
        self.optimalMasterTargetSpinBox.setObjectName("optimalMasterTargetSpinBox")
        self.horizontalLayout.addWidget(self.optimalMasterTargetSpinBox)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout_3.addWidget(self.studyPlanGroup)
        self.frequencyListGroup = QtWidgets.QGroupBox(ReadabilitySettingsDialog)
        self.frequencyListGroup.setObjectName("frequencyListGroup")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.frequencyListGroup)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.fillAllMorphsCheckBox = QtWidgets.QCheckBox(self.frequencyListGroup)
        self.fillAllMorphsCheckBox.setMinimumSize(QtCore.QSize(0, 0))
        self.fillAllMorphsCheckBox.setStatusTip("")
        self.fillAllMorphsCheckBox.setObjectName("fillAllMorphsCheckBox")
        self.verticalLayout_2.addWidget(self.fillAllMorphsCheckBox)
        self.verticalLayout_3.addWidget(self.frequencyListGroup)
        self.wordReportGroup = QtWidgets.QGroupBox(ReadabilitySettingsDialog)
        self.wordReportGroup.setObjectName("wordReportGroup")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.wordReportGroup)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.saveMissingWordsCheckBox = QtWidgets.QCheckBox(self.wordReportGroup)
        self.saveMissingWordsCheckBox.setObjectName("saveMissingWordsCheckBox")
        self.verticalLayout_5.addWidget(self.saveMissingWordsCheckBox)
        self.saveSeparateWordReportsCheckBox = QtWidgets.QCheckBox(self.wordReportGroup)
        self.saveSeparateWordReportsCheckBox.setObjectName("saveSeparateWordReportsCheckBox")
        self.verticalLayout_5.addWidget(self.saveSeparateWordReportsCheckBox)
        self.saveReadabilityDBCheckBox = QtWidgets.QCheckBox(self.wordReportGroup)
        self.saveReadabilityDBCheckBox.setObjectName("saveReadabilityDBCheckBox")
        self.verticalLayout_5.addWidget(self.saveReadabilityDBCheckBox)
        self.verticalLayout_3.addWidget(self.wordReportGroup)
        self.extrasGroup = QtWidgets.QGroupBox(ReadabilitySettingsDialog)
        self.extrasGroup.setObjectName("extrasGroup")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.extrasGroup)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.migakuDictionaryTagsCheckBox = QtWidgets.QCheckBox(self.extrasGroup)
        self.migakuDictionaryTagsCheckBox.setChecked(False)
        self.migakuDictionaryTagsCheckBox.setObjectName("migakuDictionaryTagsCheckBox")
        self.verticalLayout_4.addWidget(self.migakuDictionaryTagsCheckBox)
        self.webServiceCheckBox = QtWidgets.QCheckBox(self.extrasGroup)
        self.webServiceCheckBox.setMinimumSize(QtCore.QSize(0, 0))
        self.webServiceCheckBox.setStatusTip("")
        self.webServiceCheckBox.setObjectName("webServiceCheckBox")
        self.verticalLayout_4.addWidget(self.webServiceCheckBox)
        self.verticalLayout_3.addWidget(self.extrasGroup)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_3.addItem(spacerItem1)
        self.buttonBox = QtWidgets.QDialogButtonBox(ReadabilitySettingsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel|QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_3.addWidget(self.buttonBox)

        self.retranslateUi(ReadabilitySettingsDialog)
        self.buttonBox.accepted.connect(ReadabilitySettingsDialog.accept) # type: ignore
        self.buttonBox.rejected.connect(ReadabilitySettingsDialog.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(ReadabilitySettingsDialog)

    def retranslateUi(self, ReadabilitySettingsDialog):
        _translate = QtCore.QCoreApplication.translate
        ReadabilitySettingsDialog.setWindowTitle(_translate("ReadabilitySettingsDialog", "Advanced Settings"))
        self.studyPlanGroup.setTitle(_translate("ReadabilitySettingsDialog", "Study Plan"))
        self.alwaysAddMinimumFreqCheckBox.setToolTip(_translate("ReadabilitySettingsDialog", "Always add Minimum Frequency morphs to the study plan,\n"
"even if it exceeds the readability \'Target %\'."))
        self.alwaysAddMinimumFreqCheckBox.setText(_translate("ReadabilitySettingsDialog", "Always add Minimum Frequency morphs"))
        self.alwaysMeetReadTargettCheckBox.setToolTip(_translate("ReadabilitySettingsDialog", "Always add enough morphs to the Study Plan to meet the readability \'Target %\'\n"
"even if morphemes are below the \'Minimum Frequency\'.\n"
"\n"
"\'Minimum Frequency\' morphs still take priority."))
        self.alwaysMeetReadTargettCheckBox.setText(_translate("ReadabilitySettingsDialog", "Always meet Target %"))
        self.resetLearnedAfterEachInputCheckBox.setToolTip(_translate("ReadabilitySettingsDialog", "Default study plans assume you learn the words in each input before moving on to the next.\n"
"This option clears that learning.\n"
"\n"
"Using this option is useful for analysis rather than for use as an acutal study plan."))
        self.resetLearnedAfterEachInputCheckBox.setText(_translate("ReadabilitySettingsDialog", "Reset learned morphs after each input"))
        self.optimalMasterTargetLabel.setText(_translate("ReadabilitySettingsDialog", "Generate optimal order to Master Readability:"))
        self.optimalMasterTargetSpinBox.setSuffix(_translate("ReadabilitySettingsDialog", "%"))
        self.frequencyListGroup.setTitle(_translate("ReadabilitySettingsDialog", "Frequency Lists"))
        self.fillAllMorphsCheckBox.setToolTip(_translate("ReadabilitySettingsDialog", "When generating a study plan, by default only those morphemes that are in the plan are added to your \'frequency.txt\'.\n"
"This option includes all other morphemes at the your frequency list, enabling you to study ahead if desired."))
        self.fillAllMorphsCheckBox.setText(_translate("ReadabilitySettingsDialog", "Add all missing morphemes at the end of the Frequency List"))
        self.wordReportGroup.setTitle(_translate("ReadabilitySettingsDialog", "Word Reports"))
        self.saveMissingWordsCheckBox.setToolTip(_translate("ReadabilitySettingsDialog", "Save a report including any unknown morphs in the Master Frequency List.\n"
"\n"
"Outputs:\n"
" - missing_master_word_report.txt"))
        self.saveMissingWordsCheckBox.setText(_translate("ReadabilitySettingsDialog", "Save Missing Words Report"))
        self.saveSeparateWordReportsCheckBox.setToolTip(_translate("ReadabilitySettingsDialog", "Output a word report for each input.\n"
"\n"
"Outputs:\n"
" - a \'word_reports\' directory with a word report per input source."))
        self.saveSeparateWordReportsCheckBox.setText(_translate("ReadabilitySettingsDialog", "Save a Word Report for each input"))
        self.saveReadabilityDBCheckBox.setToolTip(_translate("ReadabilitySettingsDialog", "Generare a readability corpus database.\n"
"\n"
"Outputs:\n"
" - word_corpus.corpusdb"))
        self.saveReadabilityDBCheckBox.setText(_translate("ReadabilitySettingsDialog", "Save Readability Corpus DB"))
        self.extrasGroup.setTitle(_translate("ReadabilitySettingsDialog", "Extras"))
        self.migakuDictionaryTagsCheckBox.setToolTip(_translate("ReadabilitySettingsDialog", "Add MorphMan frequency tags to Migaku Dictionary entries.\n"
"Requires Migaku Dictionary to be installed."))
        self.migakuDictionaryTagsCheckBox.setText(_translate("ReadabilitySettingsDialog", "Migaku Dictionary Tags"))
        self.webServiceCheckBox.setToolTip(_translate("ReadabilitySettingsDialog", "Enables a WebSocket Service, allowing external apps to use MorphMan services.\n"
"Requires re-opening the Readability Analyzer to take effect."))
        self.webServiceCheckBox.setText(_translate("ReadabilitySettingsDialog", "Enable Web Service (beta)"))

# -*- coding: utf-8 -*-



# Form implementation generated from reading ui file 'morph/readability.ui'

#

# Created by: PyQt5 UI code generator 5.15.1

#

# WARNING: Any manual changes made to this file will be lost when pyuic5 is

# run again.  Do not edit this file unless you know what you are doing.





from PyQt5 import QtCore, QtGui, QtWidgets





class Ui_ReadabilityDialog(object):

    def setupUi(self, ReadabilityDialog):

        ReadabilityDialog.setObjectName("ReadabilityDialog")

        ReadabilityDialog.resize(898, 781)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        sizePolicy.setHorizontalStretch(0)

        sizePolicy.setVerticalStretch(0)

        sizePolicy.setHeightForWidth(ReadabilityDialog.sizePolicy().hasHeightForWidth())

        ReadabilityDialog.setSizePolicy(sizePolicy)

        self.verticalLayout = QtWidgets.QVBoxLayout(ReadabilityDialog)

        self.verticalLayout.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout.setSpacing(0)

        self.verticalLayout.setObjectName("verticalLayout")

        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()

        self.horizontalLayout_2.setContentsMargins(6, 6, 6, 6)

        self.horizontalLayout_2.setObjectName("horizontalLayout_2")

        self.frame = QtWidgets.QFrame(ReadabilityDialog)

        self.frame.setMinimumSize(QtCore.QSize(730, 90))

        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)

        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)

        self.frame.setObjectName("frame")

        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.frame)

        self.verticalLayout_2.setObjectName("verticalLayout_2")

        self.inputDirectoryLabel = QtWidgets.QLabel(self.frame)

        font = QtGui.QFont()

        font.setBold(True)

        font.setWeight(75)

        self.inputDirectoryLabel.setFont(font)

        self.inputDirectoryLabel.setObjectName("inputDirectoryLabel")

        self.verticalLayout_2.addWidget(self.inputDirectoryLabel)

        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()

        self.horizontalLayout_5.setObjectName("horizontalLayout_5")

        self.inputPathButton = QtWidgets.QPushButton(self.frame)

        self.inputPathButton.setObjectName("inputPathButton")

        self.horizontalLayout_5.addWidget(self.inputPathButton)

        self.inputPathEdit = QtWidgets.QLineEdit(self.frame)

        self.inputPathEdit.setObjectName("inputPathEdit")

        self.horizontalLayout_5.addWidget(self.inputPathEdit)

        self.verticalLayout_2.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()

        self.horizontalLayout_4.setObjectName("horizontalLayout_4")

        self.dictionaryLabel = QtWidgets.QLabel(self.frame)

        self.dictionaryLabel.setObjectName("dictionaryLabel")

        self.horizontalLayout_4.addWidget(self.dictionaryLabel)

        self.morphemizerComboBox = MorphemizerComboBox(parent=self.frame)

        self.morphemizerComboBox.setObjectName("morphemizerComboBox")

        self.horizontalLayout_4.addWidget(self.morphemizerComboBox)

        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(spacerItem)

        self.minFrequencyLabel = QtWidgets.QLabel(self.frame)

        self.minFrequencyLabel.setObjectName("minFrequencyLabel")

        self.horizontalLayout_4.addWidget(self.minFrequencyLabel)

        self.minFrequencySpinBox = QtWidgets.QSpinBox(self.frame)

        self.minFrequencySpinBox.setMaximum(200000)

        self.minFrequencySpinBox.setObjectName("minFrequencySpinBox")

        self.horizontalLayout_4.addWidget(self.minFrequencySpinBox)

        self.targetLabel = QtWidgets.QLabel(self.frame)

        self.targetLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)

        self.targetLabel.setObjectName("targetLabel")

        self.horizontalLayout_4.addWidget(self.targetLabel)

        self.targetSpinBox = QtWidgets.QDoubleSpinBox(self.frame)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        sizePolicy.setHorizontalStretch(0)

        sizePolicy.setVerticalStretch(0)

        sizePolicy.setHeightForWidth(self.targetSpinBox.sizePolicy().hasHeightForWidth())

        self.targetSpinBox.setSizePolicy(sizePolicy)

        self.targetSpinBox.setLayoutDirection(QtCore.Qt.LeftToRight)

        self.targetSpinBox.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)

        self.targetSpinBox.setDecimals(1)

        self.targetSpinBox.setProperty("value", 98.0)

        self.targetSpinBox.setObjectName("targetSpinBox")

        self.horizontalLayout_4.addWidget(self.targetSpinBox)

        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_2.addWidget(self.frame)

        self.frame_2 = QtWidgets.QFrame(ReadabilityDialog)

        self.frame_2.setMinimumSize(QtCore.QSize(130, 0))

        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)

        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)

        self.frame_2.setObjectName("frame_2")

        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.frame_2)

        self.verticalLayout_4.setObjectName("verticalLayout_4")

        self.analyzeButton = QtWidgets.QPushButton(self.frame_2)

        self.analyzeButton.setDefault(True)

        self.analyzeButton.setObjectName("analyzeButton")

        self.verticalLayout_4.addWidget(self.analyzeButton)

        self.closeButton = QtWidgets.QPushButton(self.frame_2)

        self.closeButton.setDefault(False)

        self.closeButton.setObjectName("closeButton")

        self.verticalLayout_4.addWidget(self.closeButton)

        self.horizontalLayout_2.addWidget(self.frame_2)

        spacerItem1 = QtWidgets.QSpacerItem(0, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(spacerItem1)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout = QtWidgets.QHBoxLayout()

        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)

        self.horizontalLayout.setContentsMargins(6, 6, 6, 6)

        self.horizontalLayout.setObjectName("horizontalLayout")

        self.generalSettingsGroupBox = QtWidgets.QGroupBox(ReadabilityDialog)

        self.generalSettingsGroupBox.setMinimumSize(QtCore.QSize(730, 180))

        self.generalSettingsGroupBox.setObjectName("generalSettingsGroupBox")

        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.generalSettingsGroupBox)

        self.verticalLayout_3.setObjectName("verticalLayout_3")

        self.masterFreqLabel = QtWidgets.QLabel(self.generalSettingsGroupBox)

        self.masterFreqLabel.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)

        self.masterFreqLabel.setObjectName("masterFreqLabel")

        self.verticalLayout_3.addWidget(self.masterFreqLabel)

        self.horizontalLayout_MasterFrequency = QtWidgets.QHBoxLayout()

        self.horizontalLayout_MasterFrequency.setObjectName("horizontalLayout_MasterFrequency")

        self.masterFreqButton = QtWidgets.QPushButton(self.generalSettingsGroupBox)

        self.masterFreqButton.setObjectName("masterFreqButton")

        self.horizontalLayout_MasterFrequency.addWidget(self.masterFreqButton)

        self.masterFreqEdit = QtWidgets.QLineEdit(self.generalSettingsGroupBox)

        self.masterFreqEdit.setObjectName("masterFreqEdit")

        self.horizontalLayout_MasterFrequency.addWidget(self.masterFreqEdit)

        self.verticalLayout_3.addLayout(self.horizontalLayout_MasterFrequency)

        self.knownMorphsLabel = QtWidgets.QLabel(self.generalSettingsGroupBox)

        self.knownMorphsLabel.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)

        self.knownMorphsLabel.setObjectName("knownMorphsLabel")

        self.verticalLayout_3.addWidget(self.knownMorphsLabel)

        self.horizontalLayout_KnownMorphs = QtWidgets.QHBoxLayout()

        self.horizontalLayout_KnownMorphs.setObjectName("horizontalLayout_KnownMorphs")

        self.knownMorphsButton = QtWidgets.QPushButton(self.generalSettingsGroupBox)

        self.knownMorphsButton.setObjectName("knownMorphsButton")

        self.horizontalLayout_KnownMorphs.addWidget(self.knownMorphsButton)

        self.knownMorphsEdit = QtWidgets.QLineEdit(self.generalSettingsGroupBox)

        self.knownMorphsEdit.setObjectName("knownMorphsEdit")

        self.horizontalLayout_KnownMorphs.addWidget(self.knownMorphsEdit)

        self.verticalLayout_3.addLayout(self.horizontalLayout_KnownMorphs)

        self.outputFreqLabel = QtWidgets.QLabel(self.generalSettingsGroupBox)

        self.outputFreqLabel.setObjectName("outputFreqLabel")

        self.verticalLayout_3.addWidget(self.outputFreqLabel)

        self.horizontalLayout_Output = QtWidgets.QHBoxLayout()

        self.horizontalLayout_Output.setObjectName("horizontalLayout_Output")

        self.outputFrequencyButton = QtWidgets.QPushButton(self.generalSettingsGroupBox)

        self.outputFrequencyButton.setObjectName("outputFrequencyButton")

        self.horizontalLayout_Output.addWidget(self.outputFrequencyButton)

        self.outputFrequencyEdit = QtWidgets.QLineEdit(self.generalSettingsGroupBox)

        self.outputFrequencyEdit.setObjectName("outputFrequencyEdit")

        self.horizontalLayout_Output.addWidget(self.outputFrequencyEdit)

        self.verticalLayout_3.addLayout(self.horizontalLayout_Output)

        self.horizontalLayout.addWidget(self.generalSettingsGroupBox)

        self.OutputsGroupBox = QtWidgets.QGroupBox(ReadabilityDialog)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        sizePolicy.setHorizontalStretch(0)

        sizePolicy.setVerticalStretch(0)

        sizePolicy.setHeightForWidth(self.OutputsGroupBox.sizePolicy().hasHeightForWidth())

        self.OutputsGroupBox.setSizePolicy(sizePolicy)

        self.OutputsGroupBox.setMinimumSize(QtCore.QSize(150, 0))

        self.OutputsGroupBox.setObjectName("OutputsGroupBox")

        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.OutputsGroupBox)

        self.verticalLayout_5.setObjectName("verticalLayout_5")

        self.studyPlanCheckBox = QtWidgets.QCheckBox(self.OutputsGroupBox)

        self.studyPlanCheckBox.setChecked(False)

        self.studyPlanCheckBox.setObjectName("studyPlanCheckBox")

        self.verticalLayout_5.addWidget(self.studyPlanCheckBox)

        self.frequencyListCheckBox = QtWidgets.QCheckBox(self.OutputsGroupBox)

        self.frequencyListCheckBox.setChecked(False)

        self.frequencyListCheckBox.setObjectName("frequencyListCheckBox")

        self.verticalLayout_5.addWidget(self.frequencyListCheckBox)

        self.wordReportCheckBox = QtWidgets.QCheckBox(self.OutputsGroupBox)

        self.wordReportCheckBox.setChecked(False)

        self.wordReportCheckBox.setObjectName("wordReportCheckBox")

        self.verticalLayout_5.addWidget(self.wordReportCheckBox)

        self.readabilityDBCheckBox = QtWidgets.QCheckBox(self.OutputsGroupBox)

        self.readabilityDBCheckBox.setChecked(False)

        self.readabilityDBCheckBox.setObjectName("readabilityDBCheckBox")

        self.verticalLayout_5.addWidget(self.readabilityDBCheckBox)

        self.groupByDirCheckBox = QtWidgets.QCheckBox(self.OutputsGroupBox)

        self.groupByDirCheckBox.setChecked(False)

        self.groupByDirCheckBox.setObjectName("groupByDirCheckBox")

        self.verticalLayout_5.addWidget(self.groupByDirCheckBox)

        self.processLinesCheckBox = QtWidgets.QCheckBox(self.OutputsGroupBox)

        self.processLinesCheckBox.setChecked(False)

        self.processLinesCheckBox.setObjectName("processLinesCheckBox")

        self.verticalLayout_5.addWidget(self.processLinesCheckBox)

        self.horizontalLayout.addWidget(self.OutputsGroupBox, 0, QtCore.Qt.AlignTop)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()

        self.horizontalLayout_3.setContentsMargins(6, -1, 6, -1)

        self.horizontalLayout_3.setObjectName("horizontalLayout_3")

        self.tabWidget = QtWidgets.QTabWidget(ReadabilityDialog)

        self.tabWidget.setObjectName("tabWidget")

        self.tabOutputLog = QtWidgets.QWidget()

        self.tabOutputLog.setObjectName("tabOutputLog")

        self.verticalLayout_21 = QtWidgets.QVBoxLayout(self.tabOutputLog)

        self.verticalLayout_21.setObjectName("verticalLayout_21")

        self.outputText = QtWidgets.QPlainTextEdit(self.tabOutputLog)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        sizePolicy.setHorizontalStretch(0)

        sizePolicy.setVerticalStretch(0)

        sizePolicy.setHeightForWidth(self.outputText.sizePolicy().hasHeightForWidth())

        self.outputText.setSizePolicy(sizePolicy)

        self.outputText.setReadOnly(True)

        self.outputText.setObjectName("outputText")

        self.verticalLayout_21.addWidget(self.outputText)

        self.tabWidget.addTab(self.tabOutputLog, "")

        self.tabReadabilityReport = QtWidgets.QWidget()

        self.tabReadabilityReport.setObjectName("tabReadabilityReport")

        self.verticalLayout_31 = QtWidgets.QVBoxLayout(self.tabReadabilityReport)

        self.verticalLayout_31.setObjectName("verticalLayout_31")

        self.readabilityTable = CustomTableWidget(self.tabReadabilityReport)

        self.readabilityTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.readabilityTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)

        self.readabilityTable.setRowCount(0)

        self.readabilityTable.setColumnCount(0)

        self.readabilityTable.setObjectName("readabilityTable")

        self.verticalLayout_31.addWidget(self.readabilityTable)

        self.tabWidget.addTab(self.tabReadabilityReport, "")

        self.tabStudyPlan = QtWidgets.QWidget()

        self.tabStudyPlan.setObjectName("tabStudyPlan")

        self.verticalLayout_41 = QtWidgets.QVBoxLayout(self.tabStudyPlan)

        self.verticalLayout_41.setObjectName("verticalLayout_41")

        self.studyPlanTable = CustomTableWidget(self.tabStudyPlan)

        self.studyPlanTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.studyPlanTable.setObjectName("studyPlanTable")

        self.studyPlanTable.setColumnCount(0)

        self.studyPlanTable.setRowCount(0)

        self.verticalLayout_41.addWidget(self.studyPlanTable)

        self.tabWidget.addTab(self.tabStudyPlan, "")

        self.horizontalLayout_3.addWidget(self.tabWidget)

        self.verticalLayout.addLayout(self.horizontalLayout_3)



        self.retranslateUi(ReadabilityDialog)

        self.tabWidget.setCurrentIndex(1)

        QtCore.QMetaObject.connectSlotsByName(ReadabilityDialog)



    def retranslateUi(self, ReadabilityDialog):

        _translate = QtCore.QCoreApplication.translate

        ReadabilityDialog.setWindowTitle(_translate("ReadabilityDialog", "Morph Man Readability Analyzer"))

        self.inputDirectoryLabel.setText(_translate("ReadabilityDialog", "Input Directory"))

        self.inputPathButton.setText(_translate("ReadabilityDialog", "..."))

        self.dictionaryLabel.setText(_translate("ReadabilityDialog", "Morphemizer:"))

        self.minFrequencyLabel.setText(_translate("ReadabilityDialog", "Minimum Master Frequency"))

        self.targetLabel.setText(_translate("ReadabilityDialog", "Target %"))

        self.analyzeButton.setText(_translate("ReadabilityDialog", "Analyze!"))

        self.closeButton.setText(_translate("ReadabilityDialog", "Close"))

        self.generalSettingsGroupBox.setTitle(_translate("ReadabilityDialog", "General Settings"))

        self.masterFreqLabel.setText(_translate("ReadabilityDialog", "Master Frequency List"))

        self.masterFreqButton.setText(_translate("ReadabilityDialog", "..."))

        self.knownMorphsLabel.setText(_translate("ReadabilityDialog", "Known Morphs DB"))

        self.knownMorphsButton.setText(_translate("ReadabilityDialog", "..."))

        self.outputFreqLabel.setText(_translate("ReadabilityDialog", "Output Directory"))

        self.outputFrequencyButton.setText(_translate("ReadabilityDialog", "..."))

        self.OutputsGroupBox.setTitle(_translate("ReadabilityDialog", "Outputs"))

        self.studyPlanCheckBox.setText(_translate("ReadabilityDialog", "Target Study Plan"))

        self.frequencyListCheckBox.setText(_translate("ReadabilityDialog", "Frequency List"))

        self.wordReportCheckBox.setText(_translate("ReadabilityDialog", "Word Report"))

        self.readabilityDBCheckBox.setText(_translate("ReadabilityDialog", "Readability DB"))

        self.groupByDirCheckBox.setText(_translate("ReadabilityDialog", "Group By Directory"))

        self.processLinesCheckBox.setText(_translate("ReadabilityDialog", "Line Stats (slower)"))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabOutputLog), _translate("ReadabilityDialog", "Output Log"))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabReadabilityReport), _translate("ReadabilityDialog", "Readability Report"))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabStudyPlan), _translate("ReadabilityDialog", "Study Plan"))

from .UI import MorphemizerComboBox

from .customTableWidget import CustomTableWidget


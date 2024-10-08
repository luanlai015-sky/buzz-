import uuid

import pytest
from pytestqt.qtbot import QtBot
from unittest.mock import patch

from buzz.locale import _
from buzz.db.entity.transcription import Transcription
from buzz.db.entity.transcription_segment import TranscriptionSegment
from buzz.model_loader import ModelType, WhisperModelSize
from buzz.transcriber.transcriber import Task
from buzz.widgets.transcription_viewer.transcription_view_mode_tool_button import (
    TranscriptionViewModeToolButton,
    ViewMode
)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QToolButton,
    QInputDialog,
)
from buzz.widgets.transcription_viewer.transcription_segments_editor_widget import (
    TranscriptionSegmentsEditorWidget,
)
from buzz.widgets.transcription_viewer.transcription_viewer_widget import (
    TranscriptionViewerWidget,
)
from tests.audio import test_audio_path


class TestTranscriptionViewerWidget:
    @pytest.fixture()
    def transcription(
        self, transcription_dao, transcription_segment_dao
    ) -> Transcription:
        id = uuid.uuid4()
        transcription_dao.insert(
            Transcription(
                id=str(id),
                status="completed",
                file=test_audio_path,
                task=Task.TRANSCRIBE.value,
                model_type=ModelType.WHISPER.value,
                whisper_model_size=WhisperModelSize.SMALL.value,
            )
        )
        transcription_segment_dao.insert(TranscriptionSegment(40, 299, "Bien", "", str(id)))
        transcription_segment_dao.insert(
            TranscriptionSegment(299, 329, "venue dans", "", str(id))
        )

        return transcription_dao.find_by_id(str(id))

    def test_should_display_segments(
        self, qtbot: QtBot, transcription, transcription_service, shortcuts
    ):
        widget = TranscriptionViewerWidget(
            transcription, transcription_service, shortcuts
        )
        qtbot.add_widget(widget)

        assert widget.windowTitle() == "whisper-french.mp3"

        editor = widget.findChild(TranscriptionSegmentsEditorWidget)
        assert isinstance(editor, TranscriptionSegmentsEditorWidget)

        assert editor.model().index(0, 1).data() == 299
        assert editor.model().index(0, 2).data() == 40
        assert editor.model().index(0, 3).data() == "Bien"
        widget.close()

    def test_should_update_segment_text(
        self, qtbot, transcription, transcription_service, shortcuts
    ):
        widget = TranscriptionViewerWidget(
            transcription, transcription_service, shortcuts
        )
        qtbot.add_widget(widget)

        editor = widget.findChild(TranscriptionSegmentsEditorWidget)
        assert isinstance(editor, TranscriptionSegmentsEditorWidget)

        editor.model().setData(editor.model().index(0, 3), "Biens")
        widget.close()

    @patch('buzz.widgets.transcription_viewer.transcription_viewer_widget.OkEnabledInputDialog')
    def test_should_resize_segment_text(self, mock_dialog, qtbot, transcription, transcription_service, shortcuts):
        mock_dialog.return_value.exec.return_value = QInputDialog.DialogCode.Accepted
        mock_dialog.return_value.intValue.return_value = 5

        widget = TranscriptionViewerWidget(
            transcription, transcription_service, shortcuts
        )
        qtbot.add_widget(widget)

        editor = widget.findChild(TranscriptionSegmentsEditorWidget)

        assert editor.model().index(1, 1).data() == 329
        assert editor.model().index(1, 2).data() == 299
        assert editor.model().index(1, 3).data() == "venue dans"

        with qtbot.waitSignal(widget.resize_button_clicked, timeout=1000):
            qtbot.mouseClick(widget.findChild(QToolButton, "resize_button"), Qt.MouseButton.LeftButton)
            widget.resize_button_clicked.emit()

        assert editor.model().index(0, 1).data() == 299
        assert editor.model().index(0, 2).data() == 40
        assert editor.model().index(0, 3).data() == "Bien"

        assert editor.model().index(1, 1).data() == 314
        assert editor.model().index(1, 2).data() == 299
        assert editor.model().index(1, 3).data() == "venue"

        assert editor.model().index(2, 1).data() == 329
        assert editor.model().index(2, 2).data() == 314
        assert editor.model().index(2, 3).data() == "dans"

        widget.close()

    def test_text_button_changes_view_mode(
            self, qtbot, transcription, transcription_service, shortcuts
    ):
        widget = TranscriptionViewerWidget(
            transcription, transcription_service, shortcuts
        )
        qtbot.add_widget(widget)

        view_mode_tool_button = widget.findChild(TranscriptionViewModeToolButton)
        menu = view_mode_tool_button.menu()

        text_action = next(action for action in menu.actions() if action.text() == _("Text"))
        text_action.trigger()
        assert widget.view_mode == ViewMode.TEXT

        text_action = next(action for action in menu.actions() if action.text() == _("Translation"))
        text_action.trigger()
        assert widget.view_mode == ViewMode.TRANSLATION

        widget.close()

package com.dreamapp.yeonsoo

import android.Manifest
import android.os.Bundle
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File

class DreamRecordActivity : AppCompatActivity() {

    private var isRecording = false
    private lateinit var recorder: AudioRecorder
    private var autoStopJob: Job? = null

    private val reqRecPermission = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) startOrStopRecording()
        else Toast.makeText(this, "마이크 권한이 필요합니다.", Toast.LENGTH_SHORT).show()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_dream_record)
        recorder = AudioRecorder(this)

        findViewById<android.widget.Button>(R.id.micButton).setOnClickListener {
            reqRecPermission.launch(Manifest.permission.RECORD_AUDIO)
        }
    }

    private fun startOrStopRecording() {
        val statusView = findViewById<android.widget.TextView>(R.id.statusText)
        val editText = findViewById<android.widget.EditText>(R.id.dreamEditText)

        if (!isRecording) {
            // 녹음 시작
            isRecording = true
            recorder.start()
            statusView.text = "녹음 중… (최대 60초)"
            autoStopJob = lifecycleScope.launch {
                delay(60000)
                if (isRecording) startOrStopRecording()
            }
        } else {
            // 녹음 종료 + 업로드
            isRecording = false
            autoStopJob?.cancel()
            recorder.stop()
            val file = recorder.outputFile ?: return
            android.widget.Toast.makeText(
                this,
                "녹음 저장됨: ${file.absolutePath} (${file.length()} bytes)",
                android.widget.Toast.LENGTH_SHORT
            ).show()
            statusView.text = "변환 중…"
            lifecycleScope.launch {
                try {
                    val result = withContext(Dispatchers.IO) { sendToStt(file) }
                    editText.setText(result)
                    statusView.text = "완료"
                } catch (e: Exception) {
                    statusView.text = "오류: ${e.message}"
                }
            }
        }
    }

    private suspend fun sendToStt(file: File): String {
        val body = file.asRequestBody("audio/mp4".toMediaType())
        val part = MultipartBody.Part.createFormData("file", file.name, body)
        val resp = RetrofitClient.api.uploadAudio(part)
        if (!resp.isSuccessful) throw RuntimeException("HTTP ${resp.code()}")
        return resp.body()?.text.orEmpty()
    }
}

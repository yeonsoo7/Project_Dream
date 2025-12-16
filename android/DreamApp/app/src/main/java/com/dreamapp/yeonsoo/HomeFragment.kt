package com.dreamapp.yeonsoo

import android.Manifest
import android.content.Context
import android.os.Bundle
import android.os.CountDownTimer
import android.view.View
import android.view.inputmethod.InputMethodManager
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.google.android.material.button.MaterialButton
import com.google.android.material.textfield.TextInputEditText
import kotlinx.coroutines.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File

class HomeFragment : Fragment(R.layout.fragment_home) {

    private val vm: DreamViewModel by activityViewModels()

    // --- 녹음 상태 ---
    private enum class RecState { IDLE, RECORDING, UPLOADING }
    private var recState: RecState = RecState.IDLE
    private lateinit var recorder: AudioRecorder
    private var stopJob: Job? = null
    private var timer: CountDownTimer? = null

    // 권한
    private val reqRecPermission = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) toggleRecord()
        else Toast.makeText(requireContext(), "마이크 권한이 필요합니다.", Toast.LENGTH_SHORT).show()
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // 예시: userId는 임시로 고정
        val userId = "test_user"
        val month = "2025-11"

        val et = view.findViewById<TextInputEditText>(R.id.etDream)
        val btnInput = view.findViewById<MaterialButton>(R.id.btnInput)
        val btnRecord = view.findViewById<MaterialButton>(R.id.btnRecord)
        val btnGenerate = view.findViewById<MaterialButton>(R.id.btnGenerate)

        val btnOpenCalendar = view.findViewById<MaterialButton>(R.id.btnOpenCalendar)

        btnOpenCalendar.setOnClickListener {
            findNavController().navigate(R.id.action_homeFragment_to_emotionCalendarFragment)
        }

        recorder = AudioRecorder(requireContext())

        // 화면 열릴 때 한 달 감정 데이터 로드
        vm.loadCalendar(userId, month)

        lifecycleScope.launchWhenStarted {
            vm.calendarDays.collect { days ->
                // TODO: 여기서 캘린더 UI에 색 입히는 로직
                // ex) day.date == "2025-11-18"의 score를 보고 색 결정
            }
        }
        lifecycleScope.launchWhenStarted {
            vm.selectedDayDreams.collect { dreams ->
                // TODO: 아래에 RecyclerView로 꿈 리스트 표시
                // 텍스트 + 이미지 + nlg_notes[0] 등
            }
        }

        // 직접 입력 버튼: 기존 동작 유지
        btnInput.setOnClickListener {
            et.requestFocus()
            val imm = requireContext().getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
            imm.showSoftInput(et, InputMethodManager.SHOW_IMPLICIT)
            showKeyboard(et)
        }

        // 녹음하기 버튼: 토글 UI
        btnRecord.setOnClickListener {
            when (recState) {
                RecState.IDLE -> reqRecPermission.launch(Manifest.permission.RECORD_AUDIO)
                RecState.RECORDING -> toggleRecord()  // 즉시 중지
                RecState.UPLOADING -> { /* 업로드 중에는 무시 */ }
            }
        }

        // 이미지 생성
        btnGenerate.setOnClickListener {
            val text = et.text?.toString()?.trim().orEmpty()
            if (text.isBlank()) {
                Toast.makeText(requireContext(), "꿈 내용을 먼저 입력해 주세요", Toast.LENGTH_SHORT).show()
            } else {
                vm.setDreamText(text)
                vm.clearImageUrl()
                hideKeyboard(et)
                findNavController().navigate(R.id.imageResultFragment)
            }
        }

        // 초기 버튼 상태
        renderIdle()
    }

    private fun onDateSelected(date: String) {
        val userId = "test_user"
        vm.loadDreamsByDate(userId, date)
    }

    private fun toggleRecord() {
        when (recState) {
            RecState.IDLE -> startRecording()
            RecState.RECORDING -> stopAndUpload()
            RecState.UPLOADING -> Unit
        }
    }

    // --- UI 상태 렌더 ---
    private fun renderIdle() {
        val btnRecord = view?.findViewById<MaterialButton>(R.id.btnRecord) ?: return
        val btnInput = view?.findViewById<MaterialButton>(R.id.btnInput)
        val btnGenerate = view?.findViewById<MaterialButton>(R.id.btnGenerate)

        recState = RecState.IDLE
        btnRecord.isEnabled = true
        btnRecord.text = "녹음하기"
        btnRecord.icon = requireContext().getDrawable(R.drawable.ic_mic_24)
        btnInput?.isEnabled = true
        btnGenerate?.isEnabled = true
    }

    private fun renderRecording() {
        val btnRecord = view?.findViewById<MaterialButton>(R.id.btnRecord) ?: return
        val btnInput = view?.findViewById<MaterialButton>(R.id.btnInput)
        val btnGenerate = view?.findViewById<MaterialButton>(R.id.btnGenerate)

        recState = RecState.RECORDING
        btnRecord.isEnabled = true
        btnRecord.text = "⏹ 녹음 중지 (01:00)"
        btnRecord.icon = null
        btnInput?.isEnabled = false
        btnGenerate?.isEnabled = false
    }

    private fun renderUploading() {
        val btnRecord = view?.findViewById<MaterialButton>(R.id.btnRecord) ?: return
        val btnInput = view?.findViewById<MaterialButton>(R.id.btnInput)
        val btnGenerate = view?.findViewById<MaterialButton>(R.id.btnGenerate)

        recState = RecState.UPLOADING
        btnRecord.isEnabled = false
        btnRecord.text = "변환 중…"
        btnRecord.icon = null
        btnInput?.isEnabled = false
        btnGenerate?.isEnabled = false
    }

    // --- 동작 ---
    private fun startRecording() {
        renderRecording()
        recorder.start()
        Toast.makeText(requireContext(), "녹음 시작", Toast.LENGTH_SHORT).show()

        // 60초 카운트다운(버튼 텍스트에 표시)
        timer?.cancel()
        timer = object : CountDownTimer(60_000, 1_000) {
            override fun onTick(ms: Long) {
                val s = (ms / 1000).toInt()
                view?.findViewById<MaterialButton>(R.id.btnRecord)?.text =
                    "⏹ 녹음 중지 (${String.format("%02d:%02d", s / 60, s % 60)})"
            }
            override fun onFinish() {
                if (recState == RecState.RECORDING) stopAndUpload()
            }
        }.start()

        // 안전장치(혹시 타이머 취소 못했을 때)
        stopJob?.cancel()
        stopJob = viewLifecycleOwner.lifecycleScope.launch {
            delay(61_000)
            if (recState == RecState.RECORDING) stopAndUpload()
        }
    }

    private fun stopAndUpload() {
        // 녹음 정지
        timer?.cancel()
        stopJob?.cancel()
        recorder.stop()
        val file = recorder.outputFile
        if (file == null || file.length() < 1024) { // 1KB 미만은 실패로 판단
            Toast.makeText(requireContext(), "녹음 파일이 비정상입니다.", Toast.LENGTH_SHORT).show()
            renderIdle()
            return
        }

        Toast.makeText(requireContext(),
            "저장됨: ${file.name} (${file.length()} bytes)", Toast.LENGTH_SHORT).show()

        // 업로드
        renderUploading()
        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val txt = withContext(Dispatchers.IO) { sendToStt(file) }
                val et = view?.findViewById<TextInputEditText>(R.id.etDream)
                val cur = et?.text?.toString().orEmpty()
                val merged = if (cur.isBlank()) txt else (cur.trimEnd() + " " + txt)
                et?.setText(merged)
                et?.setSelection(et.text!!.length)
                Toast.makeText(requireContext(), "변환 완료", Toast.LENGTH_SHORT).show()
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "STT 오류: ${e.message}", Toast.LENGTH_LONG).show()
            } finally {
                renderIdle()
            }
        }
    }

    private suspend fun sendToStt(file: File): String {
        val body = file.asRequestBody("audio/mp4".toMediaType())
        val part = MultipartBody.Part.createFormData("file", file.name, body)
        val resp = RetrofitClient.api.uploadAudio(part)
        if (!resp.isSuccessful) throw RuntimeException("HTTP ${resp.code()}")
        return resp.body()?.text.orEmpty().trim()
    }

    private fun showKeyboard(target: View) {
        val imm = requireContext().getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
        imm.showSoftInput(target, InputMethodManager.SHOW_IMPLICIT)
    }
    private fun hideKeyboard(target: View) {
        val imm = requireContext().getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
        imm.hideSoftInputFromWindow(target.windowToken, 0)
    }

    override fun onDestroyView() {
        super.onDestroyView()
        try { recorder.stop() } catch (_: Exception) {}
        timer?.cancel()
        stopJob?.cancel()
    }
}

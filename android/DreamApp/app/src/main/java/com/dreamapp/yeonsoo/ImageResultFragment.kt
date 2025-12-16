package com.dreamapp.yeonsoo

import android.os.Bundle
import android.view.View
import android.widget.ImageView
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController   // ✅ 이것이 필요!
import coil.load
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class ImageResultFragment : Fragment(R.layout.fragment_image_result) {

    private val vm: DreamViewModel by activityViewModels()

    // RetrofitClient에 imageApi 프로퍼티가 있다면 그걸 쓰는 게 깔끔
    private val imageApi: ImageApi by lazy { RetrofitClient.imageApi }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val img = view.findViewById<ImageView>(R.id.imgResult)
        val progress = view.findViewById<ProgressBar>(R.id.progress)
        val tv = view.findViewById<TextView>(R.id.tvDreamText)

        val prompt = vm.dreamText.value?.trim().orEmpty()
        tv.text = prompt
        if (prompt.isBlank()) {
            Toast.makeText(requireContext(), "텍스트가 비어있어요.", Toast.LENGTH_SHORT).show()
            return
        }

        val cached = vm.imageUrl.value
        if (!cached.isNullOrBlank()) {
            // 이미 생성된 이미지 사용
            img.load(cached)
            return
        }

        // 이미지 생성 호출
        progress.visibility = View.VISIBLE
        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val resp = withContext(Dispatchers.IO) {
                    imageApi.generate(ImageGenReq(prompt))
                }
                if (!resp.isSuccessful) throw RuntimeException("HTTP ${resp.code()}")
                val url = resp.body()?.image_url ?: throw RuntimeException("빈 응답")
                vm.setImageUrl(url)          // 캐시에 저장
                img.load(url)  // 절대 URL 그대로 로드
            } catch (e: Exception) {
                Toast.makeText(requireContext(), "이미지 생성 실패: ${e.message}", Toast.LENGTH_LONG).show()
            } finally {
                progress.visibility = View.GONE
            }
        }

        // 감정 분석 화면으로 이동 버튼
        view.findViewById<com.google.android.material.button.MaterialButton>(R.id.btnAnalyze)
            .setOnClickListener {
                findNavController().navigate(R.id.emotionResultFragment)
            }
    }
}

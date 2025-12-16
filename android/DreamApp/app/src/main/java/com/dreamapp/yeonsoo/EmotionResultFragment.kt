package com.dreamapp.yeonsoo

import android.os.Bundle
import android.view.View
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.core.view.setPadding
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.lifecycleScope
import com.google.android.material.card.MaterialCardView
import com.google.android.material.progressindicator.LinearProgressIndicator
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlin.math.roundToInt

class EmotionResultFragment : Fragment(R.layout.fragment_emotion_result) {

    private val vm: DreamViewModel by activityViewModels()
    private val api by lazy { RetrofitClient.dreamAnalysisApi }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val cardValence = view.findViewById<MaterialCardView>(R.id.cardValence)
        val tvTopEmotion = view.findViewById<TextView>(R.id.tvTopEmotion)
        val tvValenceBig = view.findViewById<TextView>(R.id.tvValenceBig)

        val boxFacets  = view.findViewById<LinearLayout>(R.id.boxFacets)
        val tvCounsel  = view.findViewById<TextView>(R.id.tvCounseling)
        val tvIds      = view.findViewById<TextView>(R.id.tvIds)

        val text = vm.dreamText.value?.trim().orEmpty()
        if (text.isBlank()) {
            Toast.makeText(requireContext(), "분석할 텍스트가 없습니다.", Toast.LENGTH_SHORT).show()
            return
        }

        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val resp = withContext(Dispatchers.IO) {
                    api.analyze(AnalyzeReq(text = text))
                }
                if (!resp.isSuccessful) throw RuntimeException("HTTP ${resp.code()}")
                val body = resp.body() ?: throw RuntimeException("빈 응답")

                // --- Valence 표시
                val pos = ((body.valence["positive"] ?: 0.0) * 100).roundToInt()
                val neg = ((body.valence["negative"] ?: 0.0) * 100).roundToInt()
                val isPositive = pos >= neg

                tvTopEmotion.text = (if (isPositive) "😊" else "😟") +
                        "  대표 감정: " + (if (isPositive) "긍정" else "부정")
                tvValenceBig.text = "긍정 ${pos}%  /  부정 ${neg}%"
                cardValence.setCardBackgroundColor(if (isPositive) 0xFFE8F5E9.toInt() else 0xFFFFEBEE.toInt())

                // --- Facets 막대 갱신
                boxFacets.removeAllViews()
                val labelKo = mapOf(
                    "aggression" to "공격성",
                    "conflict" to "갈등",
                    "friendliness" to "우호성",
                    "sexuality" to "성적 단서",
                    "success" to "성취",
                    "misfortune" to "불운"
                )
                body.facets.entries
                    .sortedByDescending { it.value }
                    .forEach { (k, v) ->
                        val pct = (v * 100).roundToInt()

                        val row = LinearLayout(requireContext()).apply {
                            orientation = LinearLayout.VERTICAL
                            setPadding(4)
                        }

                        val facetLabel = TextView(requireContext()).apply {
                            setText("• ${labelKo[k] ?: k} : ${pct}%")
                        }

                        // ✅ 기본 생성자 사용(스타일 인자 X)
                        val bar = LinearProgressIndicator(requireContext()).apply {
                            isIndeterminate = false
                            max = 100
                            progress = pct
                            trackThickness = 12
                        }

                        row.addView(facetLabel)
                        row.addView(bar)
                        boxFacets.addView(row)
                    }

                // --- 상담형 요약
                tvCounsel.text = body.counseling_note?.trim().orEmpty()

                // --- 내부 ID
                tvIds.text = "dream_id=${body.dream_id}, analysis_id=${body.saved_analysis_id}"

            } catch (e: Exception) {
                Toast.makeText(requireContext(), "감정 분석 표시 실패: ${e.message}", Toast.LENGTH_LONG).show()
            }
        }
    }
}

package com.dreamapp.yeonsoo

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

private const val PATH = "/dreams/analyze"

data class AnalyzeReq(
    val text: String,
    val user_id: String? = null,
    val date: String? = null
)

data class AnalyzeResp(
    val valence: Map<String, Double>,
    val facets: Map<String, Double>,
    val nlg_notes: List<String>,
    val dream_id: Int?,
    val saved_analysis_id: Int?,
    val counseling_note: String?
)

interface DreamAnalysisApi {
    @POST(PATH)
    suspend fun analyze(@Body req: AnalyzeReq): Response<AnalyzeResp>
}

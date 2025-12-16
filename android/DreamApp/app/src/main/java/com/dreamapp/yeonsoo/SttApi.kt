package com.dreamapp.yeonsoo

import okhttp3.MultipartBody
import retrofit2.Response
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part

data class SttResp(val text: String, val duration_sec: Double?)

interface SttApi {
    @Multipart
    @POST("/stt")
    suspend fun uploadAudio(@Part file: MultipartBody.Part): Response<SttResp>
}

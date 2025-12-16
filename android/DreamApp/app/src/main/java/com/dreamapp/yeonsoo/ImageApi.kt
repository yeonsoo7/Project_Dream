package com.dreamapp.yeonsoo

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

data class ImageGenReq(val prompt: String)

// 응답은 두 형태 중 하나일 수 있게 널 허용(서버가 URL 또는 base64를 줄 수 있음)
data class ImageGenResp(
    val image_url: String? = null,
    val base64: String? = null
)

interface ImageApi {
    @POST("/images/image/generate")
    suspend fun generate(@Body req: ImageGenReq): Response<ImageGenResp>
}



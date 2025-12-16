package com.dreamapp.yeonsoo

data class DreamDetail(
    val id: Int,
    val date: String?,
    val text: String,
    val emotion: String?,
    val interpretation: String?,
    val images: List<String>,               // "/generated/xxx.png"
    val valence: Map<String, Double>,       // {"positive": 0.xx, "negative": 0.xx}
    val facets: Map<String, Double>,
    val nlg_notes: List<String>
)

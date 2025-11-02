# 素材管理API文档

## 📋 文档信息

**项目名称：** 观山直播素材管理API  
**API版本：** v1.0  
**更新日期：** 2025-10-31  
**Base URL:** `https://api.shanshan.com/v1`

---

## 🔑 认证

### API Key认证（推荐）
```http
Headers:
  X-API-Key: your_api_key_here
```

### Token认证（可选）
```http
Headers:
  Authorization: Bearer {token}
```

---

## 📹 视频接口

### 1. 获取视频列表

**请求：**
```http
GET /videos
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| category | string | 否 | 分类：full/highlight/song |
| sort | string | 否 | 排序：time_desc/time_asc/views_desc |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 150,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "title": "观山_2025-10-30_完整录像",
        "file_path": "/media/videos/guanshan_2025-10-30.mp4",
        "file_url": "https://cdn.shanshan.com/videos/guanshan_2025-10-30.mp4",
        "duration": 14400,
        "file_size": 5368709120,
        "resolution": "1920x1080",
        "format": "mp4",
        "thumbnail": "https://cdn.shanshan.com/thumbnails/video_1.jpg",
        "view_count": 1523,
        "download_count": 89,
        "category": "full",
        "created_at": "2025-10-30T19:01:00Z"
      }
    ]
  }
}
```

### 2. 获取视频详情

**请求：**
```http
GET /videos/{id}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "title": "观山_2025-10-30_完整录像",
    "description": "2025年10月30日晚间直播完整录像",
    "file_path": "/media/videos/guanshan_2025-10-30.mp4",
    "file_url": "https://cdn.shanshan.com/videos/guanshan_2025-10-30.mp4",
    "stream_url": "https://cdn.shanshan.com/videos/guanshan_2025-10-30/playlist.m3u8",
    "duration": 14400,
    "file_size": 5368709120,
    "resolution": "1920x1080",
    "fps": 30,
    "bitrate": 3000,
    "format": "mp4",
    "codec": "h264",
    "thumbnail": "https://cdn.shanshan.com/thumbnails/video_1.jpg",
    "preview_images": [
      "https://cdn.shanshan.com/previews/video_1_001.jpg",
      "https://cdn.shanshan.com/previews/video_1_002.jpg"
    ],
    "timeline_markers": [
      {
        "time": 0,
        "type": "chat",
        "label": "开场问候"
      },
      {
        "time": 300,
        "type": "singing",
        "label": "歌曲1"
      },
      {
        "time": 450,
        "type": "gift",
        "label": "感谢礼物"
      }
    ],
    "related_songs": [1, 3, 5, 8],
    "view_count": 1523,
    "download_count": 89,
    "category": "full",
    "status": "active",
    "created_at": "2025-10-30T19:01:00Z",
    "updated_at": "2025-10-31T10:30:00Z"
  }
}
```

### 3. 下载视频

**请求：**
```http
GET /videos/{id}/download
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| quality | string | 否 | 画质：hd/sd/ld |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "download_url": "https://cdn.shanshan.com/downloads/video_1_hd.mp4",
    "file_size": 5368709120,
    "expires_at": "2025-10-31T12:00:00Z"
  }
}
```

---

## 🎵 歌曲接口

### 1. 获取歌曲列表

**请求：**
```http
GET /songs
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认50 |
| keyword | string | 否 | 搜索歌名 |
| sort | string | 否 | 排序：time/plays/duration |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 125,
    "page": 1,
    "page_size": 50,
    "items": [
      {
        "id": 1,
        "title": "晴天",
        "video_start": 300.5,
        "video_end": 480.2,
        "duration": 179.7,
        "audio_url": "https://cdn.shanshan.com/songs/001_qingtian.mp3",
        "audio_url_hq": "https://cdn.shanshan.com/songs/001_qingtian.flac",
        "video_url": "https://cdn.shanshan.com/songs/001_qingtian.mp4",
        "lyrics_srt": "https://cdn.shanshan.com/lyrics/001_qingtian.srt",
        "lyrics_ass": "https://cdn.shanshan.com/lyrics/001_qingtian.ass",
        "thumbnail": "https://cdn.shanshan.com/thumbnails/song_1.jpg",
        "waveform": "https://cdn.shanshan.com/waveforms/song_1.json",
        "play_count": 2341,
        "download_count": 156,
        "source_video_id": 1,
        "created_at": "2025-10-30T21:05:00Z"
      }
    ]
  }
}
```

### 2. 获取歌曲详情

**请求：**
```http
GET /songs/{id}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "title": "晴天",
    "artist": "周杰伦 (翻唱)",
    "video_start": 300.5,
    "video_end": 480.2,
    "duration": 179.7,
    "audio_file": {
      "mp3": {
        "url": "https://cdn.shanshan.com/songs/001_qingtian.mp3",
        "bitrate": 320,
        "size": 5760000
      },
      "flac": {
        "url": "https://cdn.shanshan.com/songs/001_qingtian.flac",
        "bitrate": 1411,
        "size": 31640000
      }
    },
    "video_file": {
      "url": "https://cdn.shanshan.com/songs/001_qingtian.mp4",
      "resolution": "1920x1080",
      "size": 45000000
    },
    "lyrics": {
      "srt": "https://cdn.shanshan.com/lyrics/001_qingtian.srt",
      "ass": "https://cdn.shanshan.com/lyrics/001_qingtian.ass",
      "text": "故事的小黄花 从出生那年就飘着..."
    },
    "thumbnail": "https://cdn.shanshan.com/thumbnails/song_1.jpg",
    "waveform": {
      "url": "https://cdn.shanshan.com/waveforms/song_1.json",
      "samples": 1000
    },
    "metadata": {
      "genre": "流行",
      "mood": "温柔",
      "key": "C大调",
      "bpm": 72
    },
    "play_count": 2341,
    "download_count": 156,
    "favorite_count": 89,
    "source_video_id": 1,
    "created_at": "2025-10-30T21:05:00Z"
  }
}
```

### 3. 下载歌曲

**请求：**
```http
GET /songs/{id}/download
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| format | string | 是 | mp3/flac/video/srt/ass |
| quality | string | 否 | 音质：hq/normal |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "download_url": "https://cdn.shanshan.com/downloads/song_1_hq.flac",
    "file_size": 31640000,
    "expires_at": "2025-10-31T12:00:00Z"
  }
}
```

---

## 😀 表情包接口

### 1. 获取表情包列表

**请求：**
```http
GET /emojis
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认30 |
| category | string | 否 | dance/thanks/gift_effect |
| size | string | 否 | 240/300/512 |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 156,
    "page": 1,
    "page_size": 30,
    "items": [
      {
        "id": 1,
        "category": "dance",
        "file_type": "gif",
        "url": "https://cdn.shanshan.com/emojis/dance_001_240.gif",
        "thumbnail": "https://cdn.shanshan.com/emojis/thumbs/dance_001.jpg",
        "file_size": 245760,
        "width": 240,
        "height": 240,
        "duration": 2.5,
        "fps": 20,
        "source_time": 1200.5,
        "view_count": 3456,
        "download_count": 234,
        "created_at": "2025-10-31T10:15:00Z"
      }
    ]
  }
}
```

### 2. 获取表情包详情

**请求：**
```http
GET /emojis/{id}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "category": "dance",
    "category_name": "手势舞",
    "description": "开场手势舞片段",
    "file_type": "gif",
    "variants": {
      "240p": {
        "url": "https://cdn.shanshan.com/emojis/dance_001_240.gif",
        "size": 245760
      },
      "300p": {
        "url": "https://cdn.shanshan.com/emojis/dance_001_300.gif",
        "size": 384000
      },
      "512p": {
        "url": "https://cdn.shanshan.com/emojis/dance_001_512.gif",
        "size": 1048576
      },
      "static": {
        "url": "https://cdn.shanshan.com/emojis/dance_001_static.jpg",
        "size": 81920
      }
    },
    "thumbnail": "https://cdn.shanshan.com/emojis/thumbs/dance_001.jpg",
    "duration": 2.5,
    "fps": 20,
    "source_video_id": 1,
    "source_time": 1200.5,
    "tags": ["手势", "舞蹈", "开场"],
    "view_count": 3456,
    "download_count": 234,
    "favorite_count": 67,
    "created_at": "2025-10-31T10:15:00Z"
  }
}
```

### 3. 批量下载表情包

**请求：**
```http
POST /emojis/batch_download
```

**请求体：**
```json
{
  "ids": [1, 2, 3, 4, 5],
  "size": "300"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "zip_url": "https://cdn.shanshan.com/downloads/emojis_batch_20251031.zip",
    "file_count": 5,
    "total_size": 1920000,
    "expires_at": "2025-10-31T18:00:00Z"
  }
}
```

---

## 📷 照片接口

### 1. 获取照片列表

**请求：**
```http
GET /photos
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| category | string | 否 | interval/scene_change/song/gift |
| time_range | string | 否 | 时间范围 0-3600 |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 480,
    "page": 1,
    "page_size": 40,
    "items": [
      {
        "id": 1,
        "category": "song",
        "url": "https://cdn.shanshan.com/photos/screenshot_001200s.jpg",
        "thumbnail": "https://cdn.shanshan.com/photos/thumbs/screenshot_001200s.jpg",
        "file_size": 204800,
        "width": 1920,
        "height": 1080,
        "source_time": 1200.0,
        "source_video_id": 1,
        "view_count": 456,
        "download_count": 34,
        "created_at": "2025-10-31T11:20:00Z"
      }
    ]
  }
}
```

### 2. 按时间线获取照片

**请求：**
```http
GET /photos/timeline
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| video_id | int | 是 | 视频ID |
| interval | int | 否 | 间隔秒数，默认30 |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "video_id": 1,
    "video_duration": 14400,
    "interval": 30,
    "total": 480,
    "items": [
      {
        "time": 0,
        "url": "https://cdn.shanshan.com/photos/screenshot_000000s.jpg",
        "thumbnail": "https://cdn.shanshan.com/photos/thumbs/screenshot_000000s.jpg"
      },
      {
        "time": 30,
        "url": "https://cdn.shanshan.com/photos/screenshot_000030s.jpg",
        "thumbnail": "https://cdn.shanshan.com/photos/thumbs/screenshot_000030s.jpg"
      }
    ]
  }
}
```

---

## 📊 统计接口

### 1. 获取总体统计

**请求：**
```http
GET /stats/summary
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "videos": {
      "total": 150,
      "total_duration": 2160000,
      "total_size": 805306368000,
      "total_views": 234567,
      "total_downloads": 12345
    },
    "songs": {
      "total": 125,
      "total_duration": 22425,
      "total_plays": 156789,
      "total_downloads": 8901
    },
    "emojis": {
      "total": 156,
      "total_downloads": 34567
    },
    "photos": {
      "total": 480,
      "total_downloads": 6789
    },
    "users": {
      "total": 5678,
      "active_today": 234
    },
    "updated_at": "2025-10-31T12:00:00Z"
  }
}
```

### 2. 获取热门内容

**请求：**
```http
GET /stats/popular
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| type | string | 是 | video/song/emoji/photo |
| limit | int | 否 | 数量，默认10 |
| period | string | 否 | 周期：day/week/month/all |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "type": "song",
    "period": "week",
    "items": [
      {
        "id": 1,
        "title": "晴天",
        "play_count": 2341,
        "download_count": 156,
        "thumbnail": "https://cdn.shanshan.com/thumbnails/song_1.jpg"
      }
    ]
  }
}
```

### 3. 记录访问/下载

**请求：**
```http
POST /stats/track
```

**请求体：**
```json
{
  "resource_type": "song",
  "resource_id": 1,
  "action": "play",
  "user_id": 123
}
```

**响应：**
```json
{
  "code": 200,
  "message": "success"
}
```

---

## 🔍 搜索接口

### 全局搜索

**请求：**
```http
GET /search
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| q | string | 是 | 搜索关键词 |
| type | string | 否 | video/song/emoji/photo/all |
| page | int | 否 | 页码 |

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "query": "晴天",
    "total": 15,
    "results": {
      "songs": [
        {
          "id": 1,
          "title": "晴天",
          "type": "song"
        }
      ],
      "videos": [],
      "emojis": [],
      "photos": []
    }
  }
}
```

---

## ⚠️ 错误码

| 错误码 | 说明 |
|-------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

**错误响应格式：**
```json
{
  "code": 400,
  "message": "Invalid parameter: page_size must be between 1 and 100",
  "error_detail": {
    "field": "page_size",
    "value": 200,
    "constraint": "max:100"
  }
}
```

---

## 📝 使用示例

### Python示例

```python
import requests

API_BASE = "https://api.shanshan.com/v1"
API_KEY = "your_api_key_here"

headers = {
    "X-API-Key": API_KEY
}

# 获取歌曲列表
response = requests.get(
    f"{API_BASE}/songs",
    headers=headers,
    params={"page": 1, "page_size": 10}
)

songs = response.json()["data"]["items"]

# 下载歌曲
song_id = songs[0]["id"]
download_response = requests.get(
    f"{API_BASE}/songs/{song_id}/download",
    headers=headers,
    params={"format": "mp3", "quality": "hq"}
)

download_url = download_response.json()["data"]["download_url"]
```

### JavaScript示例

```javascript
const API_BASE = "https://api.shanshan.com/v1";
const API_KEY = "your_api_key_here";

// 获取表情包列表
fetch(`${API_BASE}/emojis?category=dance&page=1`, {
  headers: {
    "X-API-Key": API_KEY
  }
})
.then(response => response.json())
.then(data => {
  console.log(`总共 ${data.data.total} 个表情包`);
  data.data.items.forEach(emoji => {
    console.log(`${emoji.id}: ${emoji.url}`);
  });
});
```

### cURL示例

```bash
# 获取视频详情
curl -X GET "https://api.shanshan.com/v1/videos/1" \
  -H "X-API-Key: your_api_key_here"

# 搜索歌曲
curl -X GET "https://api.shanshan.com/v1/search?q=晴天&type=song" \
  -H "X-API-Key: your_api_key_here"
```

---

## 📌 注意事项

1. **速率限制：** 每个API Key限制 100请求/分钟
2. **下载链接：** 临时下载链接有效期1小时
3. **文件大小：** 大文件建议使用断点续传
4. **缓存：** 建议客户端缓存列表数据5分钟
5. **HTTPS：** 生产环境必须使用HTTPS

---

## 📞 技术支持

**API问题反馈：**
- 邮箱：api@shanshan.com
- 文档：https://docs.shanshan.com/api

**版本更新：**
- 当前版本：v1.0
- 更新日志：https://docs.shanshan.com/changelog




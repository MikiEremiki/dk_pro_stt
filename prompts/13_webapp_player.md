# Фаза 3, День 13: WebApp плеер: React/Vue + Telegram WebApp API

## Цель (Definition of Done)
- Разработан интерактивный веб-плеер для просмотра транскрипций с использованием React или Vue.js
- Реализована синхронизация аудио с текстом транскрипции
- Добавлена возможность редактирования транскрипции
- Реализован поиск по тексту транскрипции
- Интегрирован Telegram WebApp API для бесшовной работы в Telegram
- Реализована адаптивная верстка для корректного отображения на мобильных устройствах
- Добавлена возможность экспорта выбранных фрагментов транскрипции

## Ссылки на документацию
- [Telegram WebApp API](https://core.telegram.org/bots/webapps)
- [React Documentation](https://reactjs.org/docs/getting-started.html)
- [Vue.js Documentation](https://vuejs.org/guide/introduction.html)
- [Vite Documentation](https://vitejs.dev/guide/)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [React Router](https://reactrouter.com/en/main)

---

## 1. Техническая секция

### Описание
В этом разделе мы разработаем интерактивный веб-плеер для просмотра и редактирования транскрипций. Плеер будет интегрирован с Telegram WebApp API для бесшовной работы внутри Telegram. Основные компоненты включают:

1. **Аудиоплеер**: Воспроизведение аудио с возможностью навигации по временной шкале
2. **Текстовый редактор**: Отображение и редактирование транскрипции с подсветкой текущего сегмента
3. **Поисковая система**: Поиск по тексту транскрипции с навигацией к найденным фрагментам
4. **Интеграция с Telegram**: Использование Telegram WebApp API для взаимодействия с ботом
5. **Экспорт**: Возможность экспорта выбранных фрагментов транскрипции

Мы будем использовать React для разработки фронтенда, Vite для сборки проекта и Telegram WebApp API для интеграции с Telegram.

### Примеры кода

#### Структура проекта

```
webapp/
├── public/
│   ├── favicon.ico
│   └── index.html
├── src/
│   ├── api/
│   │   ├── index.js
│   │   └── telegram.js
│   ├── components/
│   │   ├── AudioPlayer/
│   │   │   ├── AudioPlayer.jsx
│   │   │   ├── AudioPlayer.css
│   │   │   └── index.js
│   │   ├── TranscriptionEditor/
│   │   │   ├── TranscriptionEditor.jsx
│   │   │   ├── TranscriptionEditor.css
│   │   │   └── index.js
│   │   ├── SearchBar/
│   │   │   ├── SearchBar.jsx
│   │   │   ├── SearchBar.css
│   │   │   └── index.js
│   │   ├── ExportPanel/
│   │   │   ├── ExportPanel.jsx
│   │   │   ├── ExportPanel.css
│   │   │   └── index.js
│   │   └── App.jsx
│   ├── contexts/
│   │   ├── TelegramContext.jsx
│   │   └── TranscriptionContext.jsx
│   ├── hooks/
│   │   ├── useAudio.js
│   │   ├── useTranscription.js
│   │   └── useTelegram.js
│   ├── models/
│   │   └── transcription.js
│   ├── utils/
│   │   ├── formatTime.js
│   │   └── search.js
│   ├── App.css
│   ├── index.css
│   └── main.jsx
├── .env
├── .gitignore
├── package.json
├── vite.config.js
└── README.md
```

#### Настройка проекта с Vite

```bash
# Создание проекта с Vite
npm create vite@latest webapp -- --template react

# Переход в директорию проекта
cd webapp

# Установка зависимостей
npm install

# Установка дополнительных пакетов
npm install react-router-dom axios @mantine/core @mantine/hooks @emotion/react wavesurfer.js
```

#### Конфигурация Vite

```javascript
// vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: true,
  },
});
```

#### Интеграция с Telegram WebApp API

```javascript
// src/api/telegram.js
export const initTelegramApp = () => {
  // Проверяем, что скрипт Telegram WebApp загружен
  if (!window.Telegram || !window.Telegram.WebApp) {
    console.error('Telegram WebApp is not available');
    return null;
  }

  const webApp = window.Telegram.WebApp;
  
  // Инициализация WebApp
  webApp.ready();
  
  // Настройка основных параметров
  webApp.expand();
  
  // Установка темы
  document.documentElement.className = webApp.colorScheme;
  
  return webApp;
};

export const sendDataToTelegram = (data) => {
  const webApp = window.Telegram.WebApp;
  if (webApp) {
    webApp.sendData(JSON.stringify(data));
    return true;
  }
  return false;
};

export const closeWebApp = () => {
  const webApp = window.Telegram.WebApp;
  if (webApp) {
    webApp.close();
  }
};
```

#### Контекст для Telegram WebApp

```jsx
// src/contexts/TelegramContext.jsx
import React, { createContext, useEffect, useState } from 'react';
import { initTelegramApp } from '../api/telegram';

export const TelegramContext = createContext(null);

export const TelegramProvider = ({ children }) => {
  const [webApp, setWebApp] = useState(null);
  const [initData, setInitData] = useState(null);
  const [user, setUser] = useState(null);
  const [theme, setTheme] = useState('light');

  useEffect(() => {
    // Инициализация Telegram WebApp
    const app = initTelegramApp();
    if (app) {
      setWebApp(app);
      setInitData(app.initData);
      setUser(app.initDataUnsafe?.user);
      setTheme(app.colorScheme);
      
      // Обработчик изменения темы
      app.onEvent('themeChanged', () => {
        setTheme(app.colorScheme);
        document.documentElement.className = app.colorScheme;
      });
    }
  }, []);

  const sendData = (data) => {
    if (webApp) {
      webApp.sendData(JSON.stringify(data));
      return true;
    }
    return false;
  };

  const close = () => {
    if (webApp) {
      webApp.close();
    }
  };

  const showAlert = (message) => {
    if (webApp) {
      webApp.showAlert(message);
    } else {
      alert(message);
    }
  };

  const showConfirm = (message, callback) => {
    if (webApp) {
      webApp.showConfirm(message, callback);
    } else {
      const result = confirm(message);
      callback(result);
    }
  };

  return (
    <TelegramContext.Provider
      value={{
        webApp,
        initData,
        user,
        theme,
        sendData,
        close,
        showAlert,
        showConfirm,
      }}
    >
      {children}
    </TelegramContext.Provider>
  );
};
```

#### Хук для работы с Telegram WebApp

```javascript
// src/hooks/useTelegram.js
import { useContext } from 'react';
import { TelegramContext } from '../contexts/TelegramContext';

export const useTelegram = () => {
  const context = useContext(TelegramContext);
  
  if (!context) {
    throw new Error('useTelegram must be used within a TelegramProvider');
  }
  
  return context;
};
```

#### API для работы с транскрипциями

```javascript
// src/api/index.js
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Получение транскрипции по ID
export const getTranscription = async (taskId) => {
  try {
    const response = await api.get(`/tasks/${taskId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching transcription:', error);
    throw error;
  }
};

// Получение аудиофайла по ID
export const getAudioFile = async (taskId) => {
  try {
    const response = await api.get(`/tasks/${taskId}/audio`, {
      responseType: 'blob',
    });
    return URL.createObjectURL(response.data);
  } catch (error) {
    console.error('Error fetching audio file:', error);
    throw error;
  }
};

// Обновление транскрипции
export const updateTranscription = async (taskId, transcription) => {
  try {
    const response = await api.put(`/tasks/${taskId}/transcription`, transcription);
    return response.data;
  } catch (error) {
    console.error('Error updating transcription:', error);
    throw error;
  }
};

// Экспорт транскрипции
export const exportTranscription = async (taskId, format) => {
  try {
    const response = await api.get(`/exports/download`, {
      params: {
        task_id: taskId,
        format: format,
      },
      responseType: 'blob',
    });
    
    // Создаем URL для скачивания
    const url = URL.createObjectURL(response.data);
    
    // Определяем имя файла
    const contentDisposition = response.headers['content-disposition'];
    let filename = `transcription.${format}`;
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="(.+)"/);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1];
      }
    }
    
    return { url, filename };
  } catch (error) {
    console.error('Error exporting transcription:', error);
    throw error;
  }
};
```

#### Модель транскрипции

```javascript
// src/models/transcription.js
export class Segment {
  constructor(data) {
    this.id = data.id;
    this.start = data.start;
    this.end = data.end;
    this.text = data.text;
    this.speaker = data.speaker;
    this.confidence = data.confidence;
  }
  
  // Форматирование времени в формате MM:SS
  formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  
  // Получение отформатированного временного диапазона
  get timeRange() {
    return `${this.formatTime(this.start)} - ${this.formatTime(this.end)}`;
  }
  
  // Получение длительности сегмента в секундах
  get duration() {
    return this.end - this.start;
  }
  
  // Проверка, содержит ли сегмент указанное время
  containsTime(time) {
    return time >= this.start && time <= this.end;
  }
  
  // Проверка, содержит ли сегмент указанный текст
  containsText(text) {
    return this.text.toLowerCase().includes(text.toLowerCase());
  }
}

export class Transcription {
  constructor(data) {
    this.text = data.text;
    this.segments = data.segments.map(segment => new Segment(segment));
    this.language = data.language;
    this.speakers_count = data.speakers_count;
  }
  
  // Получение сегмента по времени
  getSegmentAtTime(time) {
    return this.segments.find(segment => segment.containsTime(time));
  }
  
  // Поиск сегментов по тексту
  searchSegments(query) {
    if (!query || query.trim() === '') {
      return [];
    }
    
    return this.segments.filter(segment => segment.containsText(query));
  }
  
  // Получение общей длительности транскрипции
  get duration() {
    if (this.segments.length === 0) {
      return 0;
    }
    
    return this.segments[this.segments.length - 1].end;
  }
  
  // Получение списка спикеров
  get speakers() {
    const speakerSet = new Set();
    
    this.segments.forEach(segment => {
      if (segment.speaker !== null && segment.speaker !== undefined) {
        speakerSet.add(segment.speaker);
      }
    });
    
    return Array.from(speakerSet).sort();
  }
}
```

#### Контекст для транскрипции

```jsx
// src/contexts/TranscriptionContext.jsx
import React, { createContext, useState, useEffect } from 'react';
import { getTranscription, getAudioFile } from '../api';
import { Transcription } from '../models/transcription';

export const TranscriptionContext = createContext(null);

export const TranscriptionProvider = ({ children, taskId }) => {
  const [transcription, setTranscription] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [currentSegment, setCurrentSegment] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');

  // Загрузка транскрипции и аудиофайла
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Загрузка транскрипции
        const transcriptionData = await getTranscription(taskId);
        const transcriptionModel = new Transcription(transcriptionData.result);
        setTranscription(transcriptionModel);
        
        // Загрузка аудиофайла
        const audioFileUrl = await getAudioFile(taskId);
        setAudioUrl(audioFileUrl);
        
        setLoading(false);
      } catch (err) {
        setError(err.message || 'Failed to load transcription');
        setLoading(false);
      }
    };
    
    if (taskId) {
      fetchData();
    }
  }, [taskId]);

  // Обновление текущего сегмента при изменении времени
  useEffect(() => {
    if (transcription && currentTime >= 0) {
      const segment = transcription.getSegmentAtTime(currentTime);
      setCurrentSegment(segment);
    }
  }, [transcription, currentTime]);

  // Поиск по транскрипции
  const search = (query) => {
    setSearchQuery(query);
    
    if (!transcription || !query || query.trim() === '') {
      setSearchResults([]);
      return;
    }
    
    const results = transcription.searchSegments(query);
    setSearchResults(results);
    return results;
  };

  // Переход к определенному времени
  const seekToTime = (time) => {
    setCurrentTime(time);
  };

  // Переход к определенному сегменту
  const seekToSegment = (segment) => {
    if (segment) {
      setCurrentTime(segment.start);
    }
  };

  // Обновление текста сегмента
  const updateSegmentText = (segmentId, newText) => {
    if (!transcription) return;
    
    const updatedSegments = transcription.segments.map(segment => {
      if (segment.id === segmentId) {
        return { ...segment, text: newText };
      }
      return segment;
    });
    
    const updatedTranscription = new Transcription({
      ...transcription,
      segments: updatedSegments,
      text: updatedSegments.map(s => s.text).join(' ')
    });
    
    setTranscription(updatedTranscription);
  };

  return (
    <TranscriptionContext.Provider
      value={{
        transcription,
        audioUrl,
        loading,
        error,
        currentTime,
        currentSegment,
        searchResults,
        searchQuery,
        setCurrentTime,
        seekToTime,
        seekToSegment,
        search,
        updateSegmentText,
      }}
    >
      {children}
    </TranscriptionContext.Provider>
  );
};
```

#### Хук для работы с транскрипцией

```javascript
// src/hooks/useTranscription.js
import { useContext } from 'react';
import { TranscriptionContext } from '../contexts/TranscriptionContext';

export const useTranscription = () => {
  const context = useContext(TranscriptionContext);
  
  if (!context) {
    throw new Error('useTranscription must be used within a TranscriptionProvider');
  }
  
  return context;
};
```

#### Компонент аудиоплеера

```jsx
// src/components/AudioPlayer/AudioPlayer.jsx
import React, { useEffect, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';
import { useTranscription } from '../../hooks/useTranscription';
import './AudioPlayer.css';

const AudioPlayer = () => {
  const { audioUrl, currentTime, setCurrentTime, transcription } = useTranscription();
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [playbackRate, setPlaybackRate] = useState(1);
  
  const waveformRef = useRef(null);
  const wavesurferRef = useRef(null);
  
  // Инициализация WaveSurfer
  useEffect(() => {
    if (!audioUrl || !waveformRef.current) return;
    
    // Создание экземпляра WaveSurfer
    const wavesurfer = WaveSurfer.create({
      container: waveformRef.current,
      waveColor: '#4a9eff',
      progressColor: '#1e6abc',
      cursorColor: '#333',
      barWidth: 2,
      barRadius: 3,
      cursorWidth: 1,
      height: 80,
      barGap: 2,
      responsive: true,
    });
    
    // Загрузка аудиофайла
    wavesurfer.load(audioUrl);
    
    // Обработчики событий
    wavesurfer.on('ready', () => {
      wavesurferRef.current = wavesurfer;
      setDuration(wavesurfer.getDuration());
      wavesurfer.setVolume(volume);
      wavesurfer.setPlaybackRate(playbackRate);
    });
    
    wavesurfer.on('play', () => {
      setIsPlaying(true);
    });
    
    wavesurfer.on('pause', () => {
      setIsPlaying(false);
    });
    
    wavesurfer.on('audioprocess', (time) => {
      setCurrentTime(time);
    });
    
    wavesurfer.on('seek', (progress) => {
      const time = progress * wavesurfer.getDuration();
      setCurrentTime(time);
    });
    
    // Очистка при размонтировании
    return () => {
      if (wavesurferRef.current) {
        wavesurferRef.current.destroy();
      }
    };
  }, [audioUrl]);
  
  // Обновление времени воспроизведения при изменении currentTime извне
  useEffect(() => {
    if (wavesurferRef.current && !isPlaying) {
      const currentProgress = currentTime / duration;
      wavesurferRef.current.seekTo(currentProgress);
    }
  }, [currentTime, isPlaying, duration]);
  
  // Обновление громкости
  useEffect(() => {
    if (wavesurferRef.current) {
      wavesurferRef.current.setVolume(volume);
    }
  }, [volume]);
  
  // Обновление скорости воспроизведения
  useEffect(() => {
    if (wavesurferRef.current) {
      wavesurferRef.current.setPlaybackRate(playbackRate);
    }
  }, [playbackRate]);
  
  // Форматирование времени
  const formatTime = (time) => {
    if (!time) return '00:00';
    
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };
  
  // Обработчики кнопок управления
  const handlePlayPause = () => {
    if (wavesurferRef.current) {
      wavesurferRef.current.playPause();
    }
  };
  
  const handleStop = () => {
    if (wavesurferRef.current) {
      wavesurferRef.current.stop();
      setIsPlaying(false);
    }
  };
  
  const handleVolumeChange = (e) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
  };
  
  const handlePlaybackRateChange = (rate) => {
    setPlaybackRate(rate);
  };
  
  const handleSkipBackward = () => {
    if (wavesurferRef.current) {
      const newTime = Math.max(0, currentTime - 5);
      setCurrentTime(newTime);
      wavesurferRef.current.seekTo(newTime / duration);
    }
  };
  
  const handleSkipForward = () => {
    if (wavesurferRef.current) {
      const newTime = Math.min(duration, currentTime + 5);
      setCurrentTime(newTime);
      wavesurferRef.current.seekTo(newTime / duration);
    }
  };
  
  return (
    <div className="audio-player">
      <div className="waveform-container" ref={waveformRef}></div>
      
      <div className="controls">
        <div className="time-display">
          <span>{formatTime(currentTime)}</span>
          <span> / </span>
          <span>{formatTime(duration)}</span>
        </div>
        
        <div className="playback-controls">
          <button onClick={handleSkipBackward} title="Назад 5 секунд">
            <i className="fas fa-backward"></i>
          </button>
          
          <button onClick={handlePlayPause} className="play-pause-button">
            {isPlaying ? (
              <i className="fas fa-pause"></i>
            ) : (
              <i className="fas fa-play"></i>
            )}
          </button>
          
          <button onClick={handleStop} title="Стоп">
            <i className="fas fa-stop"></i>
          </button>
          
          <button onClick={handleSkipForward} title="Вперед 5 секунд">
            <i className="fas fa-forward"></i>
          </button>
        </div>
        
        <div className="volume-control">
          <i className={`fas ${volume === 0 ? 'fa-volume-mute' : 'fa-volume-up'}`}></i>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={volume}
            onChange={handleVolumeChange}
          />
        </div>
        
        <div className="playback-rate">
          <select
            value={playbackRate}
            onChange={(e) => handlePlaybackRateChange(parseFloat(e.target.value))}
          >
            <option value="0.5">0.5x</option>
            <option value="0.75">0.75x</option>
            <option value="1">1x</option>
            <option value="1.25">1.25x</option>
            <option value="1.5">1.5x</option>
            <option value="2">2x</option>
          </select>
        </div>
      </div>
    </div>
  );
};

export default AudioPlayer;
```

#### Компонент редактора транскрипции

```jsx
// src/components/TranscriptionEditor/TranscriptionEditor.jsx
import React, { useState, useEffect, useRef } from 'react';
import { useTranscription } from '../../hooks/useTranscription';
import './TranscriptionEditor.css';

const TranscriptionEditor = () => {
  const {
    transcription,
    currentSegment,
    seekToSegment,
    updateSegmentText,
    searchResults,
    searchQuery,
  } = useTranscription();
  
  const [editingSegmentId, setEditingSegmentId] = useState(null);
  const [editText, setEditText] = useState('');
  const editorRef = useRef(null);
  const currentSegmentRef = useRef(null);
  
  // Прокрутка к текущему сегменту
  useEffect(() => {
    if (currentSegment && currentSegmentRef.current) {
      currentSegmentRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });
    }
  }, [currentSegment]);
  
  // Обработчик клика по сегменту
  const handleSegmentClick = (segment) => {
    seekToSegment(segment);
  };
  
  // Обработчик двойного клика для редактирования
  const handleSegmentDoubleClick = (segment) => {
    setEditingSegmentId(segment.id);
    setEditText(segment.text);
  };
  
  // Сохранение изменений
  const handleSaveEdit = () => {
    if (editingSegmentId !== null) {
      updateSegmentText(editingSegmentId, editText);
      setEditingSegmentId(null);
      setEditText('');
    }
  };
  
  // Отмена редактирования
  const handleCancelEdit = () => {
    setEditingSegmentId(null);
    setEditText('');
  };
  
  // Обработчик нажатия клавиш при редактировании
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSaveEdit();
    } else if (e.key === 'Escape') {
      handleCancelEdit();
    }
  };
  
  // Проверка, является ли сегмент результатом поиска
  const isSearchResult = (segment) => {
    if (!searchQuery || searchQuery.trim() === '') {
      return false;
    }
    
    return searchResults.some(result => result.id === segment.id);
  };
  
  // Подсветка текста поиска в сегменте
  const highlightSearchText = (text, query) => {
    if (!query || query.trim() === '') {
      return text;
    }
    
    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    
    return (
      <>
        {parts.map((part, i) => 
          part.toLowerCase() === query.toLowerCase() ? (
            <span key={i} className="search-highlight">{part}</span>
          ) : (
            part
          )
        )}
      </>
    );
  };
  
  if (!transcription) {
    return <div className="transcription-editor-loading">Loading transcription...</div>;
  }
  
  return (
    <div className="transcription-editor" ref={editorRef}>
      {transcription.segments.map((segment) => (
        <div
          key={segment.id}
          className={`segment ${currentSegment?.id === segment.id ? 'current' : ''} ${
            isSearchResult(segment) ? 'search-result' : ''
          }`}
          onClick={() => handleSegmentClick(segment)}
          onDoubleClick={() => handleSegmentDoubleClick(segment)}
          ref={currentSegment?.id === segment.id ? currentSegmentRef : null}
        >
          <div className="segment-header">
            <span className="segment-time">{segment.timeRange}</span>
            {segment.speaker !== null && segment.speaker !== undefined && (
              <span className={`segment-speaker speaker-${segment.speaker % 10}`}>
                Speaker {segment.speaker + 1}
              </span>
            )}
          </div>
          
          <div className="segment-content">
            {editingSegmentId === segment.id ? (
              <div className="segment-edit">
                <textarea
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  autoFocus
                />
                <div className="segment-edit-actions">
                  <button onClick={handleSaveEdit}>Save</button>
                  <button onClick={handleCancelEdit}>Cancel</button>
                </div>
              </div>
            ) : (
              <p className="segment-text">
                {highlightSearchText(segment.text, searchQuery)}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default TranscriptionEditor;
```

#### Компонент поиска

```jsx
// src/components/SearchBar/SearchBar.jsx
import React, { useState, useEffect } from 'react';
import { useTranscription } from '../../hooks/useTranscription';
import './SearchBar.css';

const SearchBar = () => {
  const { search, searchResults, seekToSegment } = useTranscription();
  const [query, setQuery] = useState('');
  const [currentResultIndex, setCurrentResultIndex] = useState(-1);
  
  // Обновление поиска при изменении запроса
  useEffect(() => {
    const delaySearch = setTimeout(() => {
      search(query);
      setCurrentResultIndex(-1);
    }, 300);
    
    return () => clearTimeout(delaySearch);
  }, [query, search]);
  
  // Обработчик изменения поискового запроса
  const handleQueryChange = (e) => {
    setQuery(e.target.value);
  };
  
  // Переход к следующему результату
  const handleNextResult = () => {
    if (searchResults.length === 0) return;
    
    const nextIndex = currentResultIndex >= searchResults.length - 1 ? 0 : currentResultIndex + 1;
    setCurrentResultIndex(nextIndex);
    seekToSegment(searchResults[nextIndex]);
  };
  
  // Переход к предыдущему результату
  const handlePrevResult = () => {
    if (searchResults.length === 0) return;
    
    const prevIndex = currentResultIndex <= 0 ? searchResults.length - 1 : currentResultIndex - 1;
    setCurrentResultIndex(prevIndex);
    seekToSegment(searchResults[prevIndex]);
  };
  
  // Очистка поиска
  const handleClearSearch = () => {
    setQuery('');
    search('');
    setCurrentResultIndex(-1);
  };
  
  return (
    <div className="search-bar">
      <div className="search-input-container">
        <input
          type="text"
          value={query}
          onChange={handleQueryChange}
          placeholder="Search in transcription..."
          className="search-input"
        />
        
        {query && (
          <button className="clear-search" onClick={handleClearSearch}>
            ×
          </button>
        )}
      </div>
      
      <div className="search-results-info">
        {searchResults.length > 0 ? (
          <>
            <span>
              {currentResultIndex + 1} of {searchResults.length} results
            </span>
            
            <div className="search-navigation">
              <button onClick={handlePrevResult} disabled={searchResults.length === 0}>
                ↑
              </button>
              <button onClick={handleNextResult} disabled={searchResults.length === 0}>
                ↓
              </button>
            </div>
          </>
        ) : query ? (
          <span>No results found</span>
        ) : null}
      </div>
    </div>
  );
};

export default SearchBar;
```

#### Компонент экспорта

```jsx
// src/components/ExportPanel/ExportPanel.jsx
import React, { useState } from 'react';
import { exportTranscription } from '../../api';
import { useTelegram } from '../../hooks/useTelegram';
import './ExportPanel.css';

const ExportPanel = ({ taskId }) => {
  const { showAlert } = useTelegram();
  const [exporting, setExporting] = useState(false);
  
  // Обработчик экспорта
  const handleExport = async (format) => {
    try {
      setExporting(true);
      
      const { url, filename } = await exportTranscription(taskId, format);
      
      // Создание ссылки для скачивания
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Освобождение URL
      setTimeout(() => URL.revokeObjectURL(url), 100);
      
      showAlert(`Exported successfully as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Export error:', error);
      showAlert(`Export failed: ${error.message}`);
    } finally {
      setExporting(false);
    }
  };
  
  return (
    <div className="export-panel">
      <h3>Export Transcription</h3>
      
      <div className="export-buttons">
        <button
          onClick={() => handleExport('text')}
          disabled={exporting}
          className="export-button text-button"
        >
          <i className="fas fa-file-alt"></i>
          <span>Text</span>
        </button>
        
        <button
          onClick={() => handleExport('docx')}
          disabled={exporting}
          className="export-button docx-button"
        >
          <i className="fas fa-file-word"></i>
          <span>DOCX</span>
        </button>
        
        <button
          onClick={() => handleExport('srt')}
          disabled={exporting}
          className="export-button srt-button"
        >
          <i className="fas fa-closed-captioning"></i>
          <span>SRT</span>
        </button>
        
        <button
          onClick={() => handleExport('json')}
          disabled={exporting}
          className="export-button json-button"
        >
          <i className="fas fa-file-code"></i>
          <span>JSON</span>
        </button>
      </div>
      
      {exporting && <div className="export-loading">Exporting...</div>}
    </div>
  );
};

export default ExportPanel;
```

#### Главный компонент приложения

```jsx
// src/components/App.jsx
import React, { useEffect } from 'react';
import { useTelegram } from '../hooks/useTelegram';
import { TranscriptionProvider } from '../contexts/TranscriptionContext';
import AudioPlayer from './AudioPlayer';
import TranscriptionEditor from './TranscriptionEditor';
import SearchBar from './SearchBar';
import ExportPanel from './ExportPanel';
import '../App.css';

const App = () => {
  const { webApp, theme, user } = useTelegram();
  const taskId = new URLSearchParams(window.location.search).get('taskId');
  
  // Настройка заголовка и кнопок в Telegram WebApp
  useEffect(() => {
    if (webApp) {
      // Установка заголовка
      webApp.setHeaderColor(theme === 'dark' ? '#1f1f1f' : '#ffffff');
      
      // Настройка основной кнопки
      webApp.MainButton.setText('Close Player');
      webApp.MainButton.onClick(() => {
        webApp.close();
      });
      
      // Показать основную кнопку
      webApp.MainButton.show();
    }
  }, [webApp, theme]);
  
  // Если taskId не указан, показываем сообщение об ошибке
  if (!taskId) {
    return (
      <div className="app-error">
        <h2>Error</h2>
        <p>No transcription task ID provided.</p>
      </div>
    );
  }
  
  return (
    <TranscriptionProvider taskId={taskId}>
      <div className={`app ${theme}`}>
        <header className="app-header">
          <h1>Transcription Player</h1>
          {user && <div className="user-info">Hello, {user.first_name}</div>}
        </header>
        
        <main className="app-content">
          <div className="player-section">
            <AudioPlayer />
          </div>
          
          <div className="search-section">
            <SearchBar />
          </div>
          
          <div className="transcription-section">
            <TranscriptionEditor />
          </div>
          
          <div className="export-section">
            <ExportPanel taskId={taskId} />
          </div>
        </main>
      </div>
    </TranscriptionProvider>
  );
};

export default App;
```

#### Точка входа приложения

```jsx
// src/main.jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './components/App';
import { TelegramProvider } from './contexts/TelegramContext';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <TelegramProvider>
      <App />
    </TelegramProvider>
  </React.StrictMode>
);
```

### Конфигурации

#### Настройка Telegram бота для работы с WebApp

```python
# src/bot/handlers/webapp.py
from aiogram import Router, F
from aiogram.types import Message, WebAppInfo
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.config import settings

router = Router()

@router.message(Command("webapp"))
async def cmd_webapp(message: Message):
    """Handler for /webapp command."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Open WebApp Player",
        web_app=WebAppInfo(url=f"{settings.WEBAPP_URL}")
    )
    
    await message.answer(
        "Click the button below to open the WebApp player:",
        reply_markup=builder.as_markup()
    )

@router.message(F.web_app_data)
async def web_app_data(message: Message):
    """Handler for data received from WebApp."""
    # Process data received from WebApp
    data = message.web_app_data.data
    await message.answer(f"Received data from WebApp: {data}")
```

#### Интеграция WebApp с диалогами бота

```python
# src/bot/dialogs/result.py
from aiogram import F
from aiogram.types import CallbackQuery, WebAppInfo
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, WebApp
from aiogram_dialog.widgets.text import Const, Format

from src.bot.states import ResultState
from src.config import settings

# ... existing code ...

# Add WebApp button to result window
result_window = Window(
    Const("📝 Результат транскрипции:"),
    Format("{text}"),
    Row(
        Button(
            Const("📥 Экспортировать"),
            id="export_result",
            on_click=on_export_selected,
            when="has_result"
        ),
        WebApp(
            Const("🎧 Открыть плеер"),
            webapp=WebAppInfo(url=f"{settings.WEBAPP_URL}?taskId={{task_id}}"),
            when="has_result"
        ),
    ),
    Row(
        Button(
            Const("🔙 В главное меню"),
            id="back_to_menu",
            on_click=lambda c, b, m: m.start(MainMenuState.main)
        )
    ),
    state=ResultState.view,
    getter=result_getter
)
```

### Схемы данных/API

#### Обновление API для поддержки WebApp

```python
# src/api/v1/endpoints/tasks.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
import tempfile
import os

from src.domains.transcription.services import TranscriptionService
from src.infrastructure.storage.object_storage import ObjectStorage
from src.api.dependencies import get_object_storage

router = APIRouter()

# ... existing code ...

@router.get("/{task_id}/audio")
async def get_task_audio(
    task_id: str,
    object_storage: ObjectStorage = Depends(get_object_storage)
) -> FileResponse:
    """Get audio file for a task."""
    try:
        # Get task details
        transcription_service = TranscriptionService(object_storage)
        task = await transcription_service.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        # Get audio file
        file_data = await object_storage.download_file(f"audio/{task_id}/audio.mp3")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix="_audio.mp3") as temp_file:
            temp_path = temp_file.name
            temp_file.write(file_data)
        
        # Return file response
        return FileResponse(
            path=temp_path,
            filename=f"{task.file_name or 'audio'}.mp3",
            media_type="audio/mpeg",
            background=lambda: os.unlink(temp_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audio file: {str(e)}")
```

## 2. Практическая секция

### Пошаговые инструкции

1. **Настройка проекта React с Vite**
   - Создайте новый проект React с использованием Vite
   - Настройте структуру проекта и основные зависимости
   - Добавьте конфигурацию для разработки и сборки

2. **Интеграция с Telegram WebApp API**
   - Добавьте скрипт Telegram WebApp в HTML-шаблон
   - Создайте контекст и хуки для работы с Telegram WebApp
   - Реализуйте базовые функции для взаимодействия с Telegram

3. **Разработка аудиоплеера**
   - Установите и настройте библиотеку WaveSurfer.js
   - Реализуйте компонент аудиоплеера с визуализацией волны
   - Добавьте элементы управления воспроизведением

4. **Создание редактора транскрипции**
   - Разработайте компонент для отображения сегментов транскрипции
   - Добавьте функциональность редактирования текста
   - Реализуйте синхронизацию с аудиоплеером

5. **Реализация поиска по транскрипции**
   - Создайте компонент поисковой строки
   - Реализуйте функцию поиска по тексту транскрипции
   - Добавьте навигацию по результатам поиска

6. **Добавление функции экспорта**
   - Реализуйте компонент панели экспорта
   - Добавьте поддержку различных форматов экспорта
   - Интегрируйте с API для скачивания файлов

7. **Стилизация и адаптивная верстка**
   - Разработайте стили для всех компонентов
   - Реализуйте адаптивную верстку для мобильных устройств
   - Добавьте поддержку светлой и темной темы

8. **Интеграция с бэкендом**
   - Настройте API-клиент для взаимодействия с бэкендом
   - Реализуйте загрузку транскрипции и аудиофайла
   - Добавьте обработку ошибок и состояний загрузки

### Частые ошибки (Common Pitfalls)

1. **Проблемы с инициализацией Telegram WebApp**
   - Убедитесь, что скрипт Telegram WebApp загружен перед использованием
   - Проверяйте наличие объекта `window.Telegram.WebApp` перед вызовом методов
   - Используйте метод `webApp.ready()` для сигнализации о готовности приложения

2. **Утечки памяти при работе с аудио**
   - Правильно уничтожайте экземпляры WaveSurfer при размонтировании компонентов
   - Освобождайте URL-объекты после использования с помощью `URL.revokeObjectURL()`
   - Используйте `useRef` для хранения ссылок на DOM-элементы и объекты

3. **Проблемы с синхронизацией аудио и текста**
   - Используйте единый источник истины для текущего времени воспроизведения
   - Избегайте циклических обновлений при синхронизации компонентов
   - Учитывайте задержки при обновлении UI и воспроизведении аудио

4. **Ошибки при работе с большими транскрипциями**
   - Реализуйте виртуализацию списка для эффективного рендеринга большого количества сегментов
   - Оптимизируйте поиск по тексту для больших объемов данных
   - Используйте дебаунсинг для предотвращения частых обновлений при поиске

5. **Проблемы с мобильной версткой**
   - Тестируйте приложение на реальных мобильных устройствах
   - Учитывайте особенности мобильных браузеров при работе с аудио
   - Адаптируйте размеры элементов управления для удобства использования на сенсорных экранах

### Советы по оптимизации (Performance Tips)

1. **Оптимизация рендеринга React-компонентов**
   - Используйте `React.memo` для предотвращения ненужных перерендеров
   - Применяйте `useCallback` и `useMemo` для мемоизации функций и вычислений
   - Разделяйте состояние на логические части для минимизации обновлений

2. **Улучшение производительности аудиоплеера**
   - Уменьшите количество точек в визуализации волны для больших файлов
   - Используйте Web Workers для обработки аудиоданных в фоновом потоке
   - Реализуйте ленивую загрузку аудиофайла по частям для больших файлов

3. **Оптимизация поиска по тексту**
   - Используйте индексацию для быстрого поиска в больших текстах
   - Применяйте дебаунсинг для предотвращения частых запросов при вводе
   - Кешируйте результаты поиска для повторных запросов

4. **Улучшение загрузки данных**
   - Реализуйте параллельную загрузку аудиофайла и транскрипции
   - Используйте кеширование для предотвращения повторных запросов
   - Добавьте прогрессивную загрузку для отображения контента по мере загрузки

5. **Оптимизация размера бандла**
   - Используйте динамический импорт для разделения кода
   - Минимизируйте зависимости и используйте tree-shaking
   - Оптимизируйте изображения и другие статические ресурсы

## 3. Валидационная секция

### Чек-лист для самопроверки

- [ ] Настроен проект React с использованием Vite
- [ ] Реализована интеграция с Telegram WebApp API
- [ ] Разработан аудиоплеер с визуализацией волны и элементами управления
- [ ] Создан редактор транскрипции с возможностью редактирования текста
- [ ] Реализован поиск по тексту транскрипции с навигацией по результатам
- [ ] Добавлена функция экспорта в различные форматы
- [ ] Реализована адаптивная верстка для мобильных устройств
- [ ] Добавлена поддержка светлой и темной темы
- [ ] Настроена интеграция с бэкендом для загрузки данных
- [ ] Реализована обработка ошибок и состояний загрузки

### Автоматизированные тесты

```jsx
// src/components/AudioPlayer/AudioPlayer.test.jsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import AudioPlayer from './AudioPlayer';
import { TranscriptionContext } from '../../contexts/TranscriptionContext';

// Mock WaveSurfer
jest.mock('wavesurfer.js', () => {
  return {
    __esModule: true,
    default: {
      create: jest.fn(() => ({
        load: jest.fn(),
        on: jest.fn((event, callback) => {
          if (event === 'ready') {
            callback();
          }
        }),
        play: jest.fn(),
        pause: jest.fn(),
        playPause: jest.fn(),
        stop: jest.fn(),
        getDuration: jest.fn(() => 100),
        setVolume: jest.fn(),
        setPlaybackRate: jest.fn(),
        seekTo: jest.fn(),
        destroy: jest.fn(),
      })),
    },
  };
});

const mockTranscriptionContext = {
  audioUrl: 'http://example.com/audio.mp3',
  currentTime: 0,
  setCurrentTime: jest.fn(),
  transcription: {
    duration: 100,
  },
};

describe('AudioPlayer', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders audio player with controls', () => {
    render(
      <TranscriptionContext.Provider value={mockTranscriptionContext}>
        <AudioPlayer />
      </TranscriptionContext.Provider>
    );

    // Check if play button is rendered
    expect(screen.getByTitle(/play/i)).toBeInTheDocument();
    
    // Check if time display is rendered
    expect(screen.getByText('00:00 / 01:40')).toBeInTheDocument();
    
    // Check if volume control is rendered
    expect(screen.getByRole('slider')).toBeInTheDocument();
  });

  test('handles play/pause button click', async () => {
    render(
      <TranscriptionContext.Provider value={mockTranscriptionContext}>
        <AudioPlayer />
      </TranscriptionContext.Provider>
    );

    // Click play button
    fireEvent.click(screen.getByTitle(/play/i));
    
    // Wait for WaveSurfer to initialize
    await waitFor(() => {
      expect(require('wavesurfer.js').default.create().playPause).toHaveBeenCalled();
    });
  });

  test('handles volume change', async () => {
    render(
      <TranscriptionContext.Provider value={mockTranscriptionContext}>
        <AudioPlayer />
      </TranscriptionContext.Provider>
    );

    // Change volume
    fireEvent.change(screen.getByRole('slider'), { target: { value: 0.5 } });
    
    // Wait for WaveSurfer to initialize
    await waitFor(() => {
      expect(require('wavesurfer.js').default.create().setVolume).toHaveBeenCalledWith(0.5);
    });
  });
});

// src/components/TranscriptionEditor/TranscriptionEditor.test.jsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import TranscriptionEditor from './TranscriptionEditor';
import { TranscriptionContext } from '../../contexts/TranscriptionContext';
import { Transcription, Segment } from '../../models/transcription';

const mockSegments = [
  new Segment({
    id: 1,
    start: 0,
    end: 5,
    text: 'Hello world',
    speaker: 0,
  }),
  new Segment({
    id: 2,
    start: 5,
    end: 10,
    text: 'This is a test',
    speaker: 1,
  }),
];

const mockTranscription = new Transcription({
  text: 'Hello world. This is a test.',
  segments: mockSegments,
  language: 'en',
  speakers_count: 2,
});

const mockTranscriptionContext = {
  transcription: mockTranscription,
  currentSegment: mockSegments[0],
  seekToSegment: jest.fn(),
  updateSegmentText: jest.fn(),
  searchResults: [],
  searchQuery: '',
};

describe('TranscriptionEditor', () => {
  test('renders transcription segments', () => {
    render(
      <TranscriptionContext.Provider value={mockTranscriptionContext}>
        <TranscriptionEditor />
      </TranscriptionContext.Provider>
    );

    // Check if segments are rendered
    expect(screen.getByText('Hello world')).toBeInTheDocument();
    expect(screen.getByText('This is a test')).toBeInTheDocument();
    
    // Check if time ranges are rendered
    expect(screen.getByText('00:00 - 00:05')).toBeInTheDocument();
    expect(screen.getByText('00:05 - 00:10')).toBeInTheDocument();
    
    // Check if speakers are rendered
    expect(screen.getByText('Speaker 1')).toBeInTheDocument();
    expect(screen.getByText('Speaker 2')).toBeInTheDocument();
  });

  test('handles segment click', () => {
    render(
      <TranscriptionContext.Provider value={mockTranscriptionContext}>
        <TranscriptionEditor />
      </TranscriptionContext.Provider>
    );

    // Click on a segment
    fireEvent.click(screen.getByText('This is a test'));
    
    // Check if seekToSegment was called with the correct segment
    expect(mockTranscriptionContext.seekToSegment).toHaveBeenCalledWith(mockSegments[1]);
  });

  test('handles segment edit', () => {
    render(
      <TranscriptionContext.Provider value={mockTranscriptionContext}>
        <TranscriptionEditor />
      </TranscriptionContext.Provider>
    );

    // Double click on a segment to edit
    fireEvent.doubleClick(screen.getByText('Hello world'));
    
    // Check if textarea appears
    const textarea = screen.getByRole('textbox');
    expect(textarea).toBeInTheDocument();
    expect(textarea.value).toBe('Hello world');
    
    // Edit text
    fireEvent.change(textarea, { target: { value: 'Hello edited world' } });
    
    // Save edit
    fireEvent.click(screen.getByText('Save'));
    
    // Check if updateSegmentText was called with the correct parameters
    expect(mockTranscriptionContext.updateSegmentText).toHaveBeenCalledWith(1, 'Hello edited world');
  });
});
```

### Критерии для ручного тестирования

1. **Тестирование интеграции с Telegram**
   - Откройте WebApp через Telegram бота
   - Проверьте, что приложение корректно инициализируется
   - Убедитесь, что тема приложения соответствует теме Telegram
   - Проверьте работу кнопок Telegram WebApp

2. **Тестирование аудиоплеера**
   - Загрузите аудиофайл и проверьте его воспроизведение
   - Протестируйте элементы управления (воспроизведение, пауза, перемотка)
   - Проверьте регулировку громкости и скорости воспроизведения
   - Убедитесь, что визуализация волны работает корректно

3. **Тестирование редактора транскрипции**
   - Проверьте отображение сегментов транскрипции
   - Протестируйте редактирование текста сегментов
   - Убедитесь, что текущий сегмент подсвечивается при воспроизведении
   - Проверьте синхронизацию между аудио и текстом

4. **Тестирование поиска**
   - Выполните поиск по различным фразам
   - Проверьте навигацию по результатам поиска
   - Убедитесь, что найденный текст подсвечивается
   - Протестируйте поиск с учетом регистра и специальных символов

5. **Тестирование экспорта**
   - Экспортируйте транскрипцию в различные форматы
   - Проверьте корректность форматирования в экспортированных файлах
   - Убедитесь, что метаданные сохраняются при экспорте
   - Протестируйте экспорт больших транскрипций

6. **Тестирование на мобильных устройствах**
   - Проверьте работу приложения на различных мобильных устройствах
   - Убедитесь, что интерфейс адаптируется к размеру экрана
   - Протестируйте сенсорное управление элементами
   - Проверьте работу в портретной и ландшафтной ориентации

7. **Тестирование производительности**
   - Загрузите большую транскрипцию (>30 минут)
   - Проверьте скорость загрузки и рендеринга
   - Убедитесь, что поиск работает быстро даже на больших текстах
   - Протестируйте работу приложения на устройствах с ограниченными ресурсами
// Индексатор evofind: параллельный обход дерева горутинами, whitelist расширений,
// исключение приватных и мусорных каталогов, поиск с ранжированием.
package main

import (
	"bufio"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"
)

// Приватность и мусор: эти каталоги никогда не индексируются.
var skipDirs = map[string]bool{
	".git": true, "node_modules": true, "__pycache__": true,
	"graphify-out": true, "go-portable": true, "go-portable-dl": true,
	"Workspace\\private": true, "Workspace/private": true, ".venv": true, "venv": true,
}

// Приватность по имени файла: секреты не индексируются никогда.
var skipFiles = map[string]bool{
	".env": true, ".env.local": true, "skills-lock.json": true,
}

var textExts = map[string]bool{
	".go": true, ".py": true, ".md": true, ".json": true, ".html": true,
	".css": true, ".js": true, ".txt": true, ".ps1": true, ".psm1": true,
	".yaml": true, ".yml": true, ".toml": true, ".cfg": true, ".ini": true,
}

const maxFileSize = 2 << 20 // 2 МБ

// Doc — один проиндексированный текстовый файл в памяти.
type Doc struct {
	Path    string   // путь относительно корня
	Ext     string   // расширение
	Lines   []string // строки файла (для сниппетов)
	Lower   []string // те же строки в lowercase (для поиска)
	ModTime int64    // unix-mtime (приоритет свежести)
	Size    int      // байт
}

// Index — набор документов + статистика последней индексации.
type Index struct {
	mu      sync.RWMutex
	docs    []*Doc
	byPath  map[string]*Doc
	Stats   Stats
}

// Stats — снимок индексации (для /stats и CLI).
type Stats struct {
	Root      string   `json:"root"`
	Files     int      `json:"files"`
	Bytes     int64    `json:"bytes"`
	DirsWalked int     `json:"dirs_walked"`
	Skipped   int      `json:"skipped"`
	Ms        float64  `json:"ms"`
	StartedAt string   `json:"started_at"`
	TopExts   []ExtCnt `json:"top_exts"`
}

type ExtCnt struct {
	Ext   string `json:"ext"`
	Count int    `json:"count"`
}

// IsTextFile решает, индексировать ли файл (расширение + не секрет + размер).
func IsTextFile(path string, size int64) bool {
	base := filepath.Base(path)
	if skipFiles[strings.ToLower(base)] {
		return false
	}
	if size > maxFileSize || size == 0 {
		return false
	}
	return textExts[strings.ToLower(filepath.Ext(path))]
}

// shouldSkip проверяет, лежит ли путь под запрещённым каталогом.
func shouldSkip(rel string) bool {
	norm := filepath.ToSlash(rel)
	for _, part := range strings.Split(norm, "/") {
		if skipDirs[part] {
			return true
		}
	}
	// приватная зона Workspace/private — на любом уровне и в любом написании
	for _, part := range strings.Split(norm, "/") {
		if part == "private" {
			return true
		}
	}
	return false
}

// readDoc читает файл в Doc (nil — файл не годится).
func readDoc(root, rel string, info os.FileInfo) *Doc {
	full := filepath.Join(root, rel)
	f, err := os.Open(full)
	if err != nil {
		return nil
	}
	defer f.Close()
	var lines, lower []string
	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 0, 64*1024), 1024*1024)
	for sc.Scan() {
		s := sc.Text()
		lines = append(lines, s)
		lower = append(lower, strings.ToLower(s))
	}
	if err := sc.Err(); err != nil {
		return nil
	}
	return &Doc{
		Path:    filepath.ToSlash(rel),
		Ext:     strings.ToLower(filepath.Ext(rel)),
		Lines:   lines,
		Lower:   lower,
		ModTime: info.ModTime().Unix(),
		Size:    int(info.Size()),
	}
}

// BuildIndex обходит root параллельно и строит индекс.
// Возвращает индекс и статистику. workerN — число горутин-читателей.
func BuildIndex(root string, workerN int) (*Index, Stats) {
	start := time.Now()
	if workerN < 2 {
		workerN = 32
	}
	idx := &Index{byPath: map[string]*Doc{}}
	st := Stats{Root: root, StartedAt: timeNow()}

	type job struct {
		rel  string
		info os.FileInfo
	}
	jobs := make(chan job, 512)
	var wg sync.WaitGroup
	var mu sync.Mutex

	reader := func() {
		defer wg.Done()
		for j := range jobs {
			if d := readDoc(root, j.rel, j.info); d != nil {
				mu.Lock()
				idx.docs = append(idx.docs, d)
				idx.byPath[d.Path] = d
				st.Files++
				st.Bytes += int64(d.Size)
				mu.Unlock()
			} else {
				mu.Lock()
				st.Skipped++
				mu.Unlock()
			}
		}
	}
	for i := 0; i < workerN; i++ {
		wg.Add(1)
		go reader()
	}

	_ = filepath.WalkDir(root, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return nil // недоступное — не фатально
		}
		rel, rerr := filepath.Rel(root, path)
		if rerr != nil {
			return nil
		}
		if rel == "." {
			return nil
		}
		if d.IsDir() {
			st.DirsWalked++
			if shouldSkip(rel) && rel != "Workspace" {
				return filepath.SkipDir
			}
			return nil
		}
		info, ierr := d.Info()
		if ierr != nil || !IsTextFile(rel, info.Size()) {
			st.Skipped++
			return nil
		}
		jobs <- job{rel: rel, info: info}
		return nil
	})
	close(jobs)
	wg.Wait()

	// топ расширений
	exts := map[string]int{}
	for _, d := range idx.docs {
		exts[d.Ext]++
	}
	for e, c := range exts {
		st.TopExts = append(st.TopExts, ExtCnt{Ext: e, Count: c})
	}
	sort.Slice(st.TopExts, func(i, j int) bool { return st.TopExts[i].Count > st.TopExts[j].Count })
	if len(st.TopExts) > 8 {
		st.TopExts = st.TopExts[:8]
	}
	st.Ms = sinceMs(start)
	return idx, st
}

// Hit — одно попадание поиска.
type Hit struct {
	Path    string `json:"path"`
	Line    int    `json:"line"`    // 1-based
	Score   int    `json:"score"`
	Snippet string `json:"snippet"`
}

// Search ищет все слова запроса (case-insensitive), ранжирует по числу вхождений
// и свежести, возвращает top-limit попаданий по файлам.
func (idx *Index) Search(query string, limit int) []Hit {
	idx.mu.RLock()
	defer idx.mu.RUnlock()
	if limit <= 0 {
		limit = 20
	}
	words := strings.Fields(strings.ToLower(query))
	if len(words) == 0 {
		return nil
	}
	type scored struct {
		doc   *Doc
		score int
		line  int
	}
	var found []scored
	for _, d := range idx.docs {
		best, bestLine := 0, 0
		total := 0
		for i, low := range d.Lower {
			lineHits := 0
			for _, w := range words {
				if strings.Contains(low, w) {
					lineHits++
				}
			}
			if lineHits == len(words) { // строка содержит ВСЕ слова
				total++
				if best == 0 {
					best, bestLine = lineHits, i+1
				}
			}
		}
		if best > 0 {
			// бонус свежести: файлы моложе 7 дней +25
			bonus := 0
			if now-d.ModTime < 7*86400 {
				bonus = 25
			}
			found = append(found, scored{doc: d, score: total*10 + bonus, line: bestLine})
		}
	}
	sort.Slice(found, func(i, j int) bool {
		if found[i].score != found[j].score {
			return found[i].score > found[j].score
		}
		return found[i].doc.ModTime > found[j].doc.ModTime
	})
	hits := make([]Hit, 0, limit)
	for i, s := range found {
		if i >= limit {
			break
		}
		hits = append(hits, Hit{
			Path: s.doc.Path, Line: s.line, Score: s.score,
			Snippet: snippet(s.doc.Lines[s.line-1], 140),
		})
	}
	return hits
}

func snippet(line string, max int) string {
	line = strings.TrimSpace(line)
	runes := []rune(line)
	if len(runes) <= max {
		return line
	}
	return string(runes[:max]) + "…"
}

// Rebuild подменяет содержимое индекса новым (для /reindex).
func (idx *Index) Rebuild(nu *Index, st Stats) {
	idx.mu.Lock()
	defer idx.mu.Unlock()
	idx.docs = nu.docs
	idx.byPath = nu.byPath
	idx.Stats = st
}

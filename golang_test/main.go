// evofind — мгновенный поиск по репозиторию Platform Evo для людей и агентов.
// Режимы:
//   evofind index  [-root DIR]                 — проиндексировать и напечатать статистику
//   evofind search -q ЗАПРОС [-root DIR] [-limit N] — разовый поиск без сервера
//   evofind serve  [-root DIR] [-port N]       — HTTP-сервер: /search?q=, /stats, POST /reindex
//
// HTTP API (только loopback):
//   GET  /search?q=текст&limit=20&ext=.py  → {"ms":…, "total":…, "hits":[{path,line,score,snippet}]}
//   GET  /stats                            → статистика индекса
//   POST /reindex                          → пересобрать индекс на лету
//
// Все поиски через HTTP дописываются в машинный журнал Platform (events.jsonl, конверт evo.tools.evofind).
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

func timeNow() string {
	return time.Now().UTC().Format("2006-01-02T15:04:05Z")
}

func sinceMs(start time.Time) float64 {
	return float64(time.Since(start).Microseconds()) / 1000.0
}

// now — точка расширения для тестов (свежесть файлов).
var now = time.Now().Unix()

const defaultRoot = `C:\Work\Platform`
const defaultPort = 8973
const eventsPath = `C:\Work\Platform\Workspace\logs\events.jsonl`

// logEvent дописывает событие в машинный журнал платформы (конверт из Л-1 data-foundation).
// Любая ошибка молча игнорируется: журнал не должен ломать поиск.
func logEvent(query string, hits int, ms float64) {
	ev := map[string]interface{}{
		"schema_id":    "evo.tools.evofind",
		"schema_version": 1,
		"produced_by":  "evofind",
		"produced_at":  timeNow(),
		"payload": map[string]interface{}{
			"kind": "evofind.query", "q": query, "hits": hits, "ms": ms,
		},
	}
	data, err := json.Marshal(ev)
	if err != nil {
		return
	}
	f, err := os.OpenFile(eventsPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
	if err != nil {
		return
	}
	defer f.Close()
	fmt.Fprintf(f, "\n%s", data)
}

func resolveRoot() string {
	root := *flagRoot
	if root == "" {
		root = defaultRoot
	}
	abs, err := filepath.Abs(root)
	if err != nil {
		return root
	}
	return abs
}

var (
	flagRoot  = flag.String("root", defaultRoot, "корень индексации")
	flagPort  = flag.Int("port", defaultPort, "порт HTTP-сервера (только loopback)")
	flagQuery = flag.String("q", "", "поисковый запрос для режима search")
	flagLimit = flag.Int("limit", 20, "максимум попаданий")
)

type searchResponse struct {
	Ms    float64 `json:"ms"`
	Total int     `json:"total"`
	Hits  []Hit   `json:"hits"`
}

func main() {
	flag.Parse()
	mode := flag.Arg(0)
	if mode == "" {
		mode = "serve"
	}

	switch mode {
	case "index":
		idx, st := BuildIndex(resolveRoot(), runtime.NumCPU()*4)
		out, _ := json.MarshalIndent(st, "", "  ")
		fmt.Println(string(out))
		_ = idx

	case "search":
		if *flagQuery == "" {
			fmt.Fprintln(os.Stderr, "укажи -q \"запрос\"")
			os.Exit(2)
		}
		idx, st := BuildIndex(resolveRoot(), runtime.NumCPU()*4)
		start := time.Now()
		hits := idx.Search(*flagQuery, *flagLimit)
		resp := searchResponse{Ms: sinceMs(start), Total: len(hits), Hits: hits}
		out, _ := json.MarshalIndent(resp, "", "  ")
		fmt.Println(string(out))
		logEvent(*flagQuery, len(hits), st.Ms+resp.Ms)

	case "serve":
		root := resolveRoot()
		fmt.Printf("[evofind] индексация %s ...\n", root)
		idx, st := BuildIndex(root, runtime.NumCPU()*4)
		out, _ := json.MarshalIndent(st, "", "  ")
		fmt.Println(string(out))

		mux := http.NewServeMux()
		mux.HandleFunc("/search", func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()
			q := strings.TrimSpace(r.URL.Query().Get("q"))
			limit := *flagLimit
			if v := r.URL.Query().Get("limit"); v != "" {
				fmt.Sscanf(v, "%d", &limit)
			}
			ext := strings.ToLower(r.URL.Query().Get("ext"))
			hits := idx.Search(q, limit)
			if ext != "" {
				filtered := hits[:0]
				for _, h := range hits {
					if strings.HasSuffix(strings.ToLower(h.Path), ext) {
						filtered = append(filtered, h)
					}
				}
				hits = filtered
			}
			resp := searchResponse{Ms: sinceMs(start), Total: len(hits), Hits: hits}
			w.Header().Set("Content-Type", "application/json; charset=utf-8")
			json.NewEncoder(w).Encode(resp)
			if q != "" {
				logEvent(q, len(hits), resp.Ms)
			}
		})
		mux.HandleFunc("/stats", func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json; charset=utf-8")
			json.NewEncoder(w).Encode(st)
		})
		mux.HandleFunc("/reindex", func(w http.ResponseWriter, r *http.Request) {
			if r.Method != http.MethodPost {
				http.Error(w, `{"error":"POST only"}`, http.StatusMethodNotAllowed)
				return
			}
			nu, ns := BuildIndex(root, runtime.NumCPU()*4)
			idx.Rebuild(nu, ns)
			w.Header().Set("Content-Type", "application/json; charset=utf-8")
			json.NewEncoder(w).Encode(ns)
		})

		addr := fmt.Sprintf("127.0.0.1:%d", *flagPort)
		fmt.Printf("[evofind] слушаю http://%s  (GET /search?q=..., /stats, POST /reindex)\n", addr)
		log.Fatal(http.ListenAndServe(addr, mux))

	default:
		fmt.Fprintln(os.Stderr, "неизвестный режим:", mode, "(доступны: index, search, serve)")
		os.Exit(2)
	}
}

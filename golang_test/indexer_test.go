// Тесты индексатора: фильтры приватности, чтение, поиск с ранжированием.
package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestShouldSkipPrivacy(t *testing.T) {
	cases := map[string]bool{
		`Workspace\private\resume\master-profile.json`: true,
		`Workspace/private/resume/x.json`:              true,
		`Workspace\private`:                            true,
		`.git\config`:                                  true,
		`node_modules\foo.js`:                          true,
		`eVo\dashboard\app.js`:                         false,
		`tools\lib\envelope.py`:                        false,
		`Docs\Map.md`:                                  false,
	}
	for path, want := range cases {
		if got := shouldSkip(path); got != want {
			t.Errorf("shouldSkip(%q) = %v, хочу %v", path, got, want)
		}
	}
}

func TestIsTextFile(t *testing.T) {
	if !IsTextFile(`Docs\Map.md`, 100) {
		t.Error(".md должен индексироваться")
	}
	if IsTextFile(`assets\logo.png`, 100) {
		t.Error(".png не должен индексироваться")
	}
	if IsTextFile(`Workspace\.env`, 100) {
		t.Error(".env не должен индексироваться никогда")
	}
	if IsTextFile(`big.json`, 10<<21) {
		t.Error("файл >2МБ не должен индексироваться")
	}
}

func TestSearchFindsWords(t *testing.T) {
	dir := t.TempDir()
	content := "поле jobs.json упоминается тут\nвторая строка без темы\njobs.json и envelope вместе\n"
	if err := os.WriteFile(filepath.Join(dir, "sample.md"), []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	idx, st := BuildIndex(dir, 4)
	if st.Files != 1 {
		t.Fatalf("хочу 1 файл, получено %d", st.Files)
	}
	hits := idx.Search("jobs.json envelope", 10)
	if len(hits) != 1 {
		t.Fatalf("хочу 1 хит (строка со всеми словами), получено %d", len(hits))
	}
	if hits[0].Line != 3 {
		t.Errorf("хочу строку 3, получено %d", hits[0].Line)
	}
	if !strings.Contains(hits[0].Snippet, "jobs.json") {
		t.Errorf("сниппет без ключевого слова: %q", hits[0].Snippet)
	}
}

func TestSearchEmptyQuery(t *testing.T) {
	dir := t.TempDir()
	_ = os.WriteFile(filepath.Join(dir, "a.txt"), []byte("x"), 0o644)
	idx, _ := BuildIndex(dir, 4)
	if hits := idx.Search("   ", 10); hits != nil {
		t.Errorf("пустой запрос должен давать nil, получено %v", hits)
	}
}

import os
from dotenv import load_dotenv
from openai import OpenAI
from langsmith import traceable

# Секреты не хранятся в коде и не попадают в коммиты (S-3, Memory/Engineering/LOG.md, 2026-10-25).
# Ключи лежат в Workspace/.env — файл не отслеживается Git (правило ".env" в .gitignore).
# Шаблон переменных: Workspace/.env.example
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# --- Настройки среды LangSmith Engine (несекретные значения) ---
os.environ.setdefault("LANGSMITH_TRACING", "true")
os.environ.setdefault("LANGSMITH_ENDPOINT", "https://eu.api.smith.langchain.com")
os.environ.setdefault("LANGSMITH_AGENT_ID", "platform-evo")
os.environ.setdefault("LANGSMITH_AGENT_ENVIRONMENT", "local")
# Заглушка для Anthropic, чтобы убрать раздражающую ошибку авторизации
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-dummy-key-for-local-dev-only-stop-complaining")

if not os.environ.get("LANGSMITH_API_KEY"):
    print("[WARN] LANGSMITH_API_KEY не найден в Workspace/.env — трассировка может не работать.")

ai_client = OpenAI(
    base_url=os.environ.get("FREE_LLM_BASE_URL", "http://localhost:31415/v1"),  # FreeLLMAPI gateway
    api_key=os.environ.get("FREE_LLM_API_KEY", "MISSING-FREE_LLM_API_KEY-in-Workspace/.env"),
)


# Главный шаг агента (Chain)
@traceable(run_type="chain", name="start_devops_agent")
def start_devops_agent(task_name: str):
    print(f"[Agent] Принял задачу в работу: {task_name}")

    # 3. Вызываем "могучую руку" ИИ для генерации конфига
    config = generate_infra_config(task_name)

    # Имитируем применение инструмента деплоя
    status = deploy_to_test_env(config)

    return f"Результат:\n{status}"


# Шаг вызова нейросети (LLM)
@traceable(run_type="llm", name="generate_infra_config")
def generate_infra_config(task: str):
    print("[LLM] Запрос к FreeLLMAPI на генерацию конфига...")

    prompt = f"Ты опытный ML DevOps инженер. Напиши лаконичный, рабочий YAML конфиг для задачи: {task}. Выведи только код."

    # Значение model="auto" заставит FreeLLMAPI автоматически выбрать лучшую
    # доступную бесплатную модель (например, Llama-3 или Gemini), у которой сейчас есть квота
    response = ai_client.chat.completions.create(
        model="auto",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    llm_output = response.choices[0].message.content
    print("[LLM] Конфиг успешно сгенерирован нейросетью!")
    return llm_output


# Шаг применения инфраструктурного инструмента (Tool)
@traceable(run_type="tool", name="deploy_to_test_env")
def deploy_to_test_env(config: str):
    # Здесь в будущем будет реальный docker-py или kubernetes-client
    return "Инфраструктура успешно развернута в локальном Docker контуре!"


if __name__ == "__main__":
    print("--- Запуск агента с реальным ИИ через FreeLLMAPI ---")
    result = start_devops_agent("deploy_nginx_cluster_with_prometheus")
    print(result)
    print("--- Проверяйте LangSmith в браузере! ---")

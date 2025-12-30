# ⚡ Pipeline de Validação Fiscal Híbrida

> **Tecnologias:** Python, Power Automate, Power Query (M), AI Builder, Excel, Azure Data Lake.
> **Status:** Em Produção (Fase de Expansão)

### O Desafio
O processo de conferência fiscal (Nota Fiscal vs. Espelho de Nota/Pedido) era realizado manualmente, consumindo cerca de **3 dias úteis** da equipe. A complexidade aumentava devido à variação de layouts de NFS-e (Notas Fiscais de Serviço) entre diferentes prefeituras, o que inviabilizava automações tradicionais rígidas.

### 💡 A Solução: Arquitetura Híbrida
Para resolver o problema de escalabilidade e tratamento de exceções, desenvolvi uma arquitetura em camadas que utiliza o "melhor de cada mundo": **Python** para processamento pesado, **Power Automate** para orquestração em nuvem e **Power Query** para regras de negócio complexas.

### 🛠️ Fluxo de Arquitetura

```mermaid
graph TD
    subgraph "1. Ingestão (Python)"
    A[🤖 Bot Python] -->|Download Arquivos| B(📂 SharePoint)
    end

    subgraph "2. Extração (Híbrida)"
    B -->|Notas Fiscais| C{⚡ Power Automate + AI}
    B -->|Notas Espelho| D{🐍 Python ETL}
    C -->|Extrai Dados| E[📄 Dados NF Brutos]
    D -->|Extrai Dados| F[📄 Dados Espelho Brutos]
    end

    subgraph "3. Transformação (Power Query)"
    E & F --> G[🗄️ Staging: Separa NF vs CTe]
    G --> H{Tratamento por Município}
    H -->|Layout A| I[L01_Cidade A]
    H -->|Layout B| J[L01_Cidade B]
    L[☁️ Azure Data Lake] -->|Dados ERP| K[Power Query]
    I & J & K --> M[⚙️ Validação de Regras]
    end

    subgraph "4. Entrega (Excel)"
    M --> N[📊 Planilha Final]
    N -->|Usuário Clica| O((🔄 Atualizar Tudo))
    end
    
    style A fill:#FFD43B,stroke:#333,stroke-width:2px
    style C fill:#0078D4,color:white,stroke:#333,stroke-width:2px
    style D fill:#FFD43B,stroke:#333,stroke-width:2px
    style G fill:#217346,color:white,stroke:#333,stroke-width:2px
    style N fill:#217346,color:white,stroke:#333,stroke-width:4px

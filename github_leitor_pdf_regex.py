# ==============================================================================
# Autora: Bruna Ferreira | GitHub: @brunafdev
# Projeto: Extrator de Dados Não-Estruturados (PDF para Excel)
# Tecnologias: PDFPlumber, Regex, Pandas
# ==============================================================================

import pdfplumber
import pandas as pd
import re
import os

# --- CONFIGURAÇÃO ---
# O script busca PDFs na pasta 'Input_PDFs' no mesmo diretório do script
PASTA_PDFS = os.path.join(os.getcwd(), "Input_PDFs")
ARQUIVO_SAIDA = "Relatorio_Consolidado_Final.xlsx" 
# --------------------

dados_finais = []

if not os.path.exists(PASTA_PDFS):
    os.makedirs(PASTA_PDFS)
    print(f"Pasta '{PASTA_PDFS}' criada. Adicione os arquivos PDF nela e rode novamente.")
else:
    print(f"Lendo arquivos em: {PASTA_PDFS}...")

    for arquivo in os.listdir(PASTA_PDFS):
        if not arquivo.endswith(".pdf"):
            continue
        
        caminho_completo = os.path.join(PASTA_PDFS, arquivo)
        
        try:
            # Extração de Texto (Layout e Puro)
            with pdfplumber.open(caminho_completo) as pdf:
                texto_padrao = ""
                for page in pdf.pages: texto_padrao += page.extract_text() + "\n"
                texto_layout = ""
                for page in pdf.pages: texto_layout += page.extract_text(layout=True) + "\n"

            # 1. PARSE DO CABEÇALHO (Dados Mestres)
            # ==
            # O PDF é dividido em blocos iniciados por "Unidade:" ou termo similar
            divisor_blocos = "Unidade:" # Ajuste conforme o padrão do seu documento
            partes = texto_padrao.split(divisor_blocos)
            
            texto_topo = partes[0]
            dados_cabecalho = {"Nome_Arquivo": arquivo}
            
            # Regex Genéricas para capturar campos chave
            # Procura por CNPJ no formato XX.XXX.XXX/XXXX-XX
            m_cnpj_prest = re.search(r"CNPJ:\s*([\d\./-]+)", texto_topo)
            # Procura linha de Prestador
            m_prestador = re.search(r"Prestador:\s*(.+)", texto_topo)
            # Procura valores monetários
            m_bruto = re.search(r"Valor Bruto \(R\$\):\s*([\d\.,]+)", texto_topo)
            m_data = re.search(r"Data Pagamento:\s*([\d/]+)", texto_topo)

            dados_cabecalho.update({
                "Prestador": m_prestador.group(1).strip() if m_prestador else "N/D",
                "CNPJ_Prestador": m_cnpj_prest.group(1) if m_cnpj_prest else "N/D",
                "Data_Ref": m_data.group(1) if m_data else "N/D",
                "Valor_Bruto": m_bruto.group(1) if m_bruto else "0,00"
            })

            # 2. PARSE DE ITENS (Blocos Repetitivos)
            # ==
            if len(partes) > 1:
                idx = 0
                for bloco in partes[1:]:
                    idx += 1
                    # Limpeza para evitar ler rodapé como item
                    bloco_limpo = bloco.split("RODAPE DO SISTEMA")[0] 
                    
                    linha = dados_cabecalho.copy()
                    linha["Item_Index"] = idx
                    
                    # Captura nome da Unidade/Filial (primeira linha do bloco)
                    linha["Unidade_Nome"] = bloco_limpo.split("\n")[0].strip()
                    
                    # Captura de valores específicos do bloco
                    m_total_unidade = re.search(r"Total \(R\$\):\s*([\d\.,]+)", bloco_limpo)
                    m_servico = re.search(r"Serviço:\s*(.+)", bloco_limpo)
                    
                    # Campo personalizado do ERP (ex: Pedido Interno / PIMS / SAP)
                    m_pedido_erp = re.search(r"PEDIDO INTERNO:\s*(\d+)", bloco_limpo)

                    linha.update({
                        "Valor_Unidade": m_total_unidade.group(1) if m_total_unidade else "0,00",
                        "Descricao_Servico": m_servico.group(1).strip() if m_servico else "",
                        "Cod_Pedido_ERP": m_pedido_erp.group(1) if m_pedido_erp else ""
                    })
                    
                    dados_finais.append(linha)

        except Exception as e:
            print(f"Erro ao processar {arquivo}: {e}")

    # 3. EXPORTAÇÃO
    # ==
    if dados_finais:
        df = pd.DataFrame(dados_finais)
        
        # Reordenação de colunas para facilitar leitura
        cols_prioridade = ['Nome_Arquivo', 'Prestador', 'CNPJ_Prestador', 'Valor_Bruto', 'Unidade_Nome', 'Valor_Unidade']
        cols_existentes = [c for c in cols_prioridade if c in df.columns]
        cols_resto = [c for c in df.columns if c not in cols_existentes]
        
        df = df[cols_existentes + cols_resto]
        
        df.to_excel(ARQUIVO_SAIDA, index=False)
        print(f"\n✅ Concluído! Dados extraídos de {len(dados_finais)} itens.")
        print(f"Arquivo salvo como: {ARQUIVO_SAIDA}")
    else:
        print("Nenhum dado foi extraído. Verifique o padrão do PDF.")

        #bfdev
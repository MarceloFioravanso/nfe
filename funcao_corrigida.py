def encontrar_proxima_nota(df):
    """
    Encontra a próxima nota a ser processada utilizando a função encontrar_notas_pendentes.
    Mantida para compatibilidade com o código existente.
    
    Args:
        df (pd.DataFrame): DataFrame com os dados do Excel
        
    Returns:
        dict: Dados da próxima nota a ser processada ou None se não encontrar
    """
    try:
        notas_pendentes = encontrar_notas_pendentes(df)
        if notas_pendentes:
            logger.info(f"Retornando a primeira nota das {len(notas_pendentes)} notas pendentes encontradas")
            return notas_pendentes[0]
        
        logger.warning("Não foi encontrada nenhuma nota pendente para processamento.")
        return None
    
    except Exception as e:
        logger.error(f"Erro ao procurar próxima nota: {e}")
        return None

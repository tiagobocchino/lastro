-- Lastro · 0007: agenda do monitoramento no pg_cron (card LST-26).
-- A cada 5 minutos: colhe a verificação anterior, verifica /saude de novo e avalia os alertas.
-- A verificação a cada 5 minutos mantém o Render acordado (substitui o lastro-acordar da 0004) e passa
-- pelo banco (/saude faz ping), então o Supabase nunca chega aos 7 dias parado que pausam o projeto.
-- Render gratuito: 750 horas de instância por mês na conta; um serviço sempre acordado usa ~744.
select cron.unschedule('lastro-acordar') where exists (select 1 from cron.job where jobname = 'lastro-acordar');
select cron.schedule('lastro-monitor', '*/5 * * * *', 'select interno.monitorar()');

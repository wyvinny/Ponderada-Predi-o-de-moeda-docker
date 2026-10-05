# Arquitetura

`backend-api` é a única borda pública e agrega `prophet-service` e `sarima-service`. `postgres` persiste pedidos de retreino e inferências; `minio-bronze` representa o lake Bronze. `mlops-worker` valida o snapshot, enquanto `training-worker` consome pedidos e valida o lote de retreino antes de qualquer promoção.

As imagens Python usam build em dois estágios (wheels e runtime sem compiladores). PostgreSQL e MinIO derivam de imagens oficiais porque são infraestrutura administrada. Todos os serviços usam a rede interna `usdbrl_internal`; a porta host é `8080` para a API.

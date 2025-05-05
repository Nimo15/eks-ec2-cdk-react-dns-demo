#!/bin/zsh

set -e

echo "🔍 Verificando se o release 'cert-manager' existe..."
helm list -n cert-manager

echo "🧹 Desinstalando release Helm 'cert-manager'..."
helm uninstall cert-manager -n cert-manager || echo "⚠️ Release já removido ou não existia"

echo "🧼 Limpando todos os recursos restantes no namespace cert-manager..."
kubectl delete all --all -n cert-manager || echo "⚠️ Nada para deletar ou namespace vazio"

echo "📦 Garantindo que o repositório Jetstack está configurado..."
helm repo add jetstack https://charts.jetstack.io || echo "✅ Repositório já existe"
helm repo update

echo "🚀 Reinstalando cert-manager com CRDs..."
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --set installCRDs=true \
  --create-namespace

echo "✅ Processo concluído. Aguarde os pods ficarem prontos:"
echo "    kubectl get pods -n cert-manager --watch"
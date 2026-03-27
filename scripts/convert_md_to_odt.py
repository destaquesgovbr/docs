#!/usr/bin/env python3
"""
Script para converter relatórios Markdown (.md) para ODT (.odt)
com renderização de diagramas Mermaid para imagens PNG.

Uso:
    python convert_md_to_odt.py <input.md> [--output output.odt]
    python convert_md_to_odt.py --all  # Converte todos .md em relatorios/

Dependências do sistema:
    - pandoc (brew install pandoc / apt install pandoc)
    - mermaid-cli (npm install -g @mermaid-js/mermaid-cli)

Dependências Python:
    - pypandoc (pip install pypandoc)
"""

import argparse
import re
import subprocess
import hashlib
import tempfile
import shutil
import sys
import zipfile
from pathlib import Path
from typing import List, Tuple

try:
    import pypandoc
except ImportError:
    print("[X] Erro: pypandoc nao esta instalado.")
    print("   Instale com: pip install pypandoc")
    print("   Ou com Poetry: poetry add pypandoc")
    sys.exit(2)


# Constantes
MERMAID_REGEX = r'```mermaid\n(.*?)```'
IMG_DIR = 'imgs'
OUTPUT_DIR = 'output'


def check_dependencies():
    """Verifica se dependências do sistema estão instaladas"""
    missing = []

    if not shutil.which('mmdc'):
        missing.append('mermaid-cli (npm install -g @mermaid-js/mermaid-cli)')

    if not shutil.which('pandoc'):
        missing.append('pandoc (brew/apt/choco install pandoc)')

    if missing:
        print("[X] Dependencias do sistema faltando:")
        for dep in missing:
            print(f"   - {dep}")
        print("\nConsulte scripts/README-convert.md para instrucoes de instalacao.")
        sys.exit(2)


class MermaidRenderer:
    """Renderiza diagramas Mermaid para PNG usando mermaid-cli"""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def render(self, mermaid_code: str, index: int) -> Path:
        """Renderiza um diagrama Mermaid e retorna o caminho da imagem"""
        # Hash do código para cache
        code_hash = hashlib.md5(mermaid_code.encode()).hexdigest()[:8]
        png_path = self.cache_dir / f"diagram-{code_hash}.png"

        # Se já existe no cache, retorna
        if png_path.exists():
            print(f"  [OK] Usando cache: {png_path.name}")
            return png_path

        # Cria arquivo temporário .mmd
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.mmd', delete=False, encoding='utf-8'
        ) as tmp:
            tmp.write(mermaid_code)
            tmp_path = Path(tmp.name)

        try:
            # Renderiza com mmdc
            result = subprocess.run(
                ['mmdc', '-i', str(tmp_path), '-o', str(png_path)],
                capture_output=True,
                text=True,
                timeout=30,
                shell=True  # Necessário no Windows para encontrar mmdc.cmd
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"Erro ao renderizar Mermaid: {result.stderr}"
                )

            print(f"  [OK] Renderizado: {png_path.name}")
            return png_path

        except subprocess.TimeoutExpired:
            print(f"  [!]  Timeout ao renderizar diagrama {index} (>30s)")
            return self.create_placeholder(f"Timeout no diagrama {index}")
        except Exception as e:
            print(f"  [!]  Erro no diagrama {index}: {e}")
            return self.create_placeholder(f"Erro ao renderizar diagrama {index}")
        finally:
            tmp_path.unlink(missing_ok=True)

    def create_placeholder(self, message: str) -> Path:
        """Cria uma imagem placeholder para diagramas com erro"""
        # Por simplicidade, criamos um arquivo de texto que será convertido
        # Em uma implementação mais robusta, poderia usar PIL para criar PNG
        placeholder_path = self.cache_dir / f"placeholder-{hashlib.md5(message.encode()).hexdigest()[:8]}.txt"
        placeholder_path.write_text(message, encoding='utf-8')
        print(f"  [!]  Placeholder criado: {placeholder_path.name}")
        return placeholder_path


class MarkdownProcessor:
    """Processa Markdown extraindo e substituindo blocos Mermaid"""

    def __init__(self, renderer: MermaidRenderer):
        self.renderer = renderer

    def remove_emojis(self, text: str) -> str:
        """Remove emojis e ícones do texto"""
        # Padrão que captura a maioria dos emojis Unicode
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"  # dingbats
            "\U000024C2-\U0001F251"  # enclosed characters
            "\U0001F900-\U0001F9FF"  # supplemental symbols
            "\U0001FA00-\U0001FA6F"  # extended symbols
            "\u2600-\u26FF"          # miscellaneous symbols
            "\u2700-\u27BF"          # dingbats
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub('', text)

    def process(self, md_content: str, img_relative_path: str) -> str:
        """Substitui blocos Mermaid por imagens e remove emojis"""
        # Remove emojis primeiro
        md_content = self.remove_emojis(md_content)

        diagram_count = 0

        def replace_mermaid(match):
            nonlocal diagram_count
            diagram_count += 1
            mermaid_code = match.group(1)

            print(f"  Processando diagrama {diagram_count}...")
            png_path = self.renderer.render(mermaid_code, diagram_count)

            # Path relativo da imagem no Markdown
            # Adiciona atributo de largura para caber na página (6in = ~15cm)
            img_md_path = f"{img_relative_path}/{png_path.name}"
            return f"![Diagrama {diagram_count}]({img_md_path}){{width=6in}}"

        processed = re.sub(
            MERMAID_REGEX,
            replace_mermaid,
            md_content,
            flags=re.DOTALL
        )

        print(f"  Total: {diagram_count} diagramas processados")
        return processed


class ODTConverter:
    """Converte Markdown para ODT usando Pandoc"""

    def add_table_borders(self, odt_path: Path):
        """Adiciona bordas horizontais nas tabelas do ODT"""
        # Diretório temporário para extrair o ODT
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)

        try:
            # Extrair ODT
            with zipfile.ZipFile(odt_path, 'r') as zf:
                zf.extractall(temp_path)

            # Ler content.xml
            content_xml = temp_path / 'content.xml'
            content = content_xml.read_text(encoding='utf-8')

            # Adicionar bordas horizontais nos estilos de células de tabela
            # Substituir fo:border="none" por bordas apenas horizontal (top e bottom)
            content = re.sub(
                r'<style:table-cell-properties fo:border="none"\s*/>',
                '<style:table-cell-properties fo:border-top="0.5pt solid #000000" fo:border-bottom="0.5pt solid #000000" fo:border-left="none" fo:border-right="none" fo:padding="0.0382in"/>',
                content
            )
            # Também substituir caso tenha espaços
            content = re.sub(
                r'<style:table-cell-properties\s+/>',
                '<style:table-cell-properties fo:border-top="0.5pt solid #000000" fo:border-bottom="0.5pt solid #000000" fo:border-left="none" fo:border-right="none" fo:padding="0.0382in"/>',
                content
            )

            # Remover sufixo de ponto dos bullets (style:num-suffix=".")
            content = re.sub(
                r'style:num-suffix="\."',
                '',
                content
            )

            # Corrigir links internos do sumário (remover prefixo id_ dos hrefs)
            # Links: xlink:href="#id_1-objetivo..." → xlink:href="#objetivo..."
            # Bookmarks: text:name="objetivo-..." (sem o prefixo id_)
            content = re.sub(
                r'xlink:href="#id_([0-9]+)-',
                r'xlink:href="#',
                content
            )
            # Também remover id_ quando não há número
            content = re.sub(
                r'xlink:href="#id_',
                r'xlink:href="#',
                content
            )

            # Salvar content.xml modificado
            content_xml.write_text(content, encoding='utf-8')

            # Reempacotar ODT
            with zipfile.ZipFile(odt_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # mimetype deve ser o primeiro, sem compressão
                mimetype_file = temp_path / 'mimetype'
                if mimetype_file.exists():
                    zf.write(mimetype_file, 'mimetype', compress_type=zipfile.ZIP_STORED)

                # Adicionar todos os outros arquivos
                for file_path in temp_path.rglob('*'):
                    if file_path.is_file() and file_path.name != 'mimetype':
                        arcname = str(file_path.relative_to(temp_path))
                        zf.write(file_path, arcname)

        finally:
            # Limpar diretório temporário
            shutil.rmtree(temp_path)

    def convert(
        self,
        md_content: str,
        output_path: Path,
        title: str = None,
        author: str = "DestaquesGovBr Team"
    ):
        """Converte Markdown para ODT"""
        # Cria arquivo temporário
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.md',
            delete=False,
            encoding='utf-8'
        ) as tmp:
            tmp.write(md_content)
            tmp_path = tmp.name

        try:
            # Caminho do arquivo de referência (template ODT com fontes customizadas)
            script_dir = Path(__file__).parent
            reference_odt = script_dir / 'templates' / 'reference.odt'

            # Metadata para Pandoc
            extra_args = [
                '--standalone',
                '--toc',  # Table of Contents
                '--toc-depth=3',
                '--wrap=auto',
                '--highlight-style=pygments',  # Syntax highlighting com cores
            ]

            # Usar arquivo de referência com fontes Arial e Courier New + fundo cinza
            if reference_odt.exists():
                extra_args.append(f'--reference-doc={reference_odt}')

            if title:
                extra_args.extend(['-M', f'title={title}'])

            extra_args.extend(['-M', f'author={author}'])

            # Conversão via pypandoc
            pypandoc.convert_file(
                tmp_path,
                'odt',
                outputfile=str(output_path),
                extra_args=extra_args
            )

            # Adicionar bordas nas tabelas
            self.add_table_borders(output_path)

            print(f"  [OK] ODT gerado: {output_path}")

        finally:
            Path(tmp_path).unlink(missing_ok=True)


def convert_single_file(
    input_path: Path,
    output_path: Path = None,
    cache_dir: Path = None
):
    """Converte um único arquivo Markdown para ODT"""

    # Paths padrão
    if output_path is None:
        output_path = input_path.parent / OUTPUT_DIR / (
            input_path.stem + '.odt'
        )

    if cache_dir is None:
        cache_dir = input_path.parent / OUTPUT_DIR / IMG_DIR

    # Cria diretórios de output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Convertendo: {input_path.name}")
    print(f"{'='*60}")

    # Lê o arquivo Markdown
    md_content = input_path.read_text(encoding='utf-8')

    # Processa Mermaid
    renderer = MermaidRenderer(cache_dir)
    processor = MarkdownProcessor(renderer)

    # Path ABSOLUTO das imagens (para que Pandoc encontre de qualquer lugar)
    img_path = str(cache_dir.absolute()).replace('\\', '/')
    processed_md = processor.process(md_content, img_path)

    # Converte para ODT
    converter = ODTConverter()
    title = input_path.stem.replace('-', ' ').title()
    converter.convert(processed_md, output_path, title=title)

    print(f"\n[OK] Conversao concluida!")
    print(f"   Output: {output_path}")


def convert_all_files(relatorios_dir: Path):
    """Converte todos os arquivos .md no diretório"""
    md_files = sorted(list(relatorios_dir.glob('*.md')))

    if not md_files:
        print(f"[X] Nenhum arquivo .md encontrado em: {relatorios_dir}")
        return 1

    print(f"\nEncontrados {len(md_files)} arquivos Markdown:")
    for f in md_files:
        print(f"  - {f.name}")

    success_count = 0
    error_count = 0

    for md_file in md_files:
        try:
            convert_single_file(md_file)
            success_count += 1
        except Exception as e:
            print(f"\n[X] Erro ao converter {md_file.name}: {e}")
            error_count += 1
            continue

    print(f"\n{'='*60}")
    print(f"Resumo: {success_count} sucesso(s), {error_count} erro(s)")
    print(f"{'='*60}")

    return 0 if error_count == 0 else 1


def main():
    parser = argparse.ArgumentParser(
        description='Converte relatórios Markdown para ODT com diagramas Mermaid renderizados',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s relatorio.md
  %(prog)s relatorio.md --output meu-relatorio.odt
  %(prog)s --all
  %(prog)s --all --relatorios-dir docs/docs/relatorios/
        """
    )
    parser.add_argument(
        'input',
        nargs='?',
        type=Path,
        help='Arquivo .md de entrada'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Arquivo .odt de saída (opcional)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Converte todos os .md no diretório de relatórios'
    )
    parser.add_argument(
        '--relatorios-dir',
        type=Path,
        default=Path('docs/docs/relatorios'),
        help='Diretório contendo os relatórios (padrão: docs/docs/relatorios)'
    )

    args = parser.parse_args()

    # Verifica dependências do sistema
    check_dependencies()

    # Validação
    if args.all:
        relatorios_dir = args.relatorios_dir
        if not relatorios_dir.exists():
            print(f"[X] Diretório não encontrado: {relatorios_dir}")
            return 1

        return convert_all_files(relatorios_dir)

    elif args.input:
        if not args.input.exists():
            print(f"[X] Arquivo não encontrado: {args.input}")
            return 1

        convert_single_file(args.input, args.output)
        return 0

    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())

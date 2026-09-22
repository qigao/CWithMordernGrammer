function Header(el)
  if FORMAT == "typst" and el.level == 1 then
    return {
      pandoc.RawBlock("typst", "#pagebreak(weak: true)"),
      el,
    }
  end
  return el
end

from PIL import Image
from rembg import remove, new_session
im = Image.open('poster.png').convert('RGB')
sess = new_session('isnet-general-use')
for name, box in {'logo': (1390, 70, 1785, 385), 'headline': (300, 195, 1075, 850)}.items():
    c = im.crop(box); c.save(f'{name}_crop.png')
    remove(c, session=sess, post_process_mask=True).save(f'{name}_cut.png')
out = Image.new('RGB', (1200, 700), (30, 110, 180))
for i, n in enumerate(['logo', 'headline']):
    c = Image.open(n + '_cut.png'); out.paste(c, (10 + i * 420, 10), c)
out.save('cut_check2.jpg')

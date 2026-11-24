import sys
from PIL import Image
from rembg import remove, new_session
src = sys.argv[1]
im = Image.open(src).convert('RGB')
sess = new_session(sys.argv[2] if len(sys.argv) > 2 else 'isnet-general-use')
# crops in poster pixels (1792x2400): x0,y0,x1,y1
crops = {'biscoff': (300, 870, 900, 2160), 'pistachio': (940, 880, 1530, 2150)}
for name, box in crops.items():
    c = im.crop(box)
    c.save(f'{name}_crop.png')
    out = remove(c, session=sess, post_process_mask=True)
    out.save(f'{name}_cut.png')
    print(name, out.size)

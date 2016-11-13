

def create_map_html(latlon_list):
    srcfile = open('mapview_src.html', 'r')
    outfile = open('mapview_out.html', 'w')
    for line in srcfile:
        if not '!!!' in line:
            outfile.write(line)
        else:
            formatted_list = ['{lat: %f, lng: %f}'%c for c in latlon_list]
            outfile.write( ',\n'.join(formatted_list) + '\n' )
    srcfile.close()
    outfile.close()

if __name__ == '__main__':
    create_map_html([(50,100), (51,100), (50.5,100.5)])

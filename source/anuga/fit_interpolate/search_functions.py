"""
General functions used in fit and interpolate.

   Ole Nielsen, Stephen Roberts, Duncan Gray
   Geoscience Australia, 2006.

"""
from Numeric import dot

from anuga.utilities.numerical_tools import get_machine_precision

def search_tree_of_vertices(root, mesh, x):
    """
    Find the triangle (element) that the point x is in.

    Inputs:
        root: A quad tree of the vertices
        mesh: The underlying mesh
        x:    The point being placed
    
    Return:
        element_found, sigma0, sigma1, sigma2, k

        where
        element_found: True if a triangle containing x was found
        sigma0, sigma1, sigma2: The interpolated values
        k: Index of triangle (if found)

    """
    #Find triangle containing x:
    element_found = False

    # This will be returned if element_found = False
    sigma2 = -10.0
    sigma0 = -10.0
    sigma1 = -10.0
    k = -10.0
            
    #Find vertices near x
    candidate_vertices = root.search(x[0], x[1])
    is_more_elements = True

    element_found, sigma0, sigma1, sigma2, k = \
                   _search_triangles_of_vertices(mesh,
                                                 candidate_vertices, x)
    while not element_found and is_more_elements:
        candidate_vertices, branch = root.expand_search()
        if branch == []:
            # Searching all the verts from the root cell that haven't
            # been searched.  This is the last try
            element_found, sigma0, sigma1, sigma2, k = \
                           _search_triangles_of_vertices(mesh,
                                                         candidate_vertices, x)
            is_more_elements = False
        else:
            element_found, sigma0, sigma1, sigma2, k = \
                       _search_triangles_of_vertices(mesh,
                                                     candidate_vertices, x)

    return element_found, sigma0, sigma1, sigma2, k

def _search_triangles_of_vertices(mesh, candidate_vertices, x):
    """Search for triangle containing x amongs candidate_vertices in mesh

    This is called by search_tree_of_vertices once the appropriate node
    has been found from the quad tree.
    

    This function is responsible for most of the compute time in
    fit and interpolate.
    """
    
    #Find triangle containing x:
    element_found = False

    # This will be returned if element_found = False
    sigma2 = -10.0
    sigma0 = -10.0
    sigma1 = -10.0
    k = -10
    
    #For all vertices in same cell as point x
    for v in candidate_vertices:
        #FIXME (DSG-DSG): this catches verts with no triangle.
        #Currently pmesh is producing these.
        #this should be stopped,

        if mesh.number_of_triangles_per_node[v] == 0:
            continue
        
        #for each triangle id (k) which has v as a vertex
        vertexlist = mesh.get_triangles_and_vertices_per_node(node=v)
        for k, _ in vertexlist:
            #Get the three vertex_points of candidate triangle k
            xi0, xi1, xi2 = mesh.get_vertex_coordinates(triangle_id=k)            

            # Get the three normals (faster than using API)
            n0 = mesh.normals[k,0:2]
            n1 = mesh.normals[k,2:4]
            n2 = mesh.normals[k,4:6]            

            
            #Compute interpolation
            sigma2 = dot((x-xi0), n2)/dot((xi2-xi0), n2)
            sigma0 = dot((x-xi1), n0)/dot((xi0-xi1), n0)
            sigma1 = dot((x-xi2), n1)/dot((xi1-xi2), n1)

            # Integrity check - machine precision is too hard
            # so we use hardwired single precision 
            epsilon = 1.0e-6
            msg = 'abs(sigma0+sigma1+sigma2-1) = %.15e, eps = %.15e'\
                  %(abs(sigma0+sigma1+sigma2-1), epsilon)
            assert abs(sigma0 + sigma1 + sigma2 - 1.0) < epsilon, msg


            #Check that this triangle contains the data point
            
            # Sigmas are allowed to get negative within
            # machine precision on some machines (e.g. nautilus)
            epsilon = get_machine_precision() * 2
            if sigma0 >= -epsilon and sigma1 >= -epsilon and sigma2 >= -epsilon:
                element_found = True
                break
            
        if element_found is True:
            # Don't look for any other triangle
            break
        
    return element_found, sigma0, sigma1, sigma2, k


